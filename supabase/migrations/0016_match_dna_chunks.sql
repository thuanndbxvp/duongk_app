-- ============================================================
-- Migration: 0016_match_dna_chunks.sql
-- Purpose: RAG retrieval với MMR (Maximal Marginal Relevance)
-- ============================================================

-- RPC function: Vector search với MMR reranking
CREATE OR REPLACE FUNCTION match_dna_chunks(
    p_assistant_id UUID,
    p_query_embedding extensions.vector(1024),
    p_top_k INT DEFAULT 10,
    p_lambda FLOAT DEFAULT 0.7,
    p_section_filter TEXT DEFAULT NULL
) RETURNS TABLE(
    chunk_id UUID,
    text TEXT,
    section TEXT,
    timestamp_start FLOAT,
    timestamp_end FLOAT,
    similarity FLOAT,
    mmr_score FLOAT
) AS $$
DECLARE
    v_result JSONB;
BEGIN
    -- Greedy MMR selection
    WITH RECURSIVE mmr_selection AS (
        -- Base case: select highest similarity chunk
        SELECT
            dc.id AS chunk_id,
            dc.text_content as text,
            dc.section,
            dc.timestamp_start_sec as timestamp_start,
            dc.timestamp_end_sec as timestamp_end,
            1 - (dc.embedding <=> p_query_embedding) AS similarity,
            (1 - (dc.embedding <=> p_query_embedding))::FLOAT AS mmr_score,
            ARRAY[dc.id] AS selected_ids,
            1 AS iteration
        FROM dna_chunks dc
        WHERE dc.assistant_id = p_assistant_id
            AND dc.expires_at > NOW()
            AND (p_section_filter IS NULL OR dc.section = p_section_filter)
        ORDER BY (dc.embedding <=> p_query_embedding) ASC
        LIMIT 1
        
        UNION ALL
        
        -- Recursive case: select based on MMR score
        SELECT
            dc.id AS chunk_id,
            dc.text_content as text,
            dc.section,
            dc.timestamp_start_sec as timestamp_start,
            dc.timestamp_end_sec as timestamp_end,
            1 - (dc.embedding <=> p_query_embedding) AS similarity,
            (p_lambda * (1 - (dc.embedding <=> p_query_embedding)) - 
             (1 - p_lambda) * COALESCE(
                 (SELECT MAX(1 - (dc.embedding <=> dc2.embedding))
                  FROM dna_chunks dc2
                  WHERE dc2.id = ANY(ms.selected_ids)),
                 0
             ))::FLOAT AS mmr_score,
            array_append(ms.selected_ids, dc.id) AS selected_ids,
            ms.iteration + 1 AS iteration
        FROM dna_chunks dc, mmr_selection ms
        WHERE dc.assistant_id = p_assistant_id
            AND dc.expires_at > NOW()
            AND (p_section_filter IS NULL OR dc.section = p_section_filter)
            AND dc.id != ALL(ms.selected_ids)
            AND ms.iteration < p_top_k
    )
    SELECT jsonb_agg(
        jsonb_build_object(
            'chunk_id', chunk_id,
            'text', text,
            'section', section,
            'timestamp_start', timestamp_start,
            'timestamp_end', timestamp_end,
            'similarity', similarity,
            'mmr_score', mmr_score
        )
    ) INTO v_result
    FROM (
        SELECT DISTINCT ON (chunk_id) *
        FROM mmr_selection
        ORDER BY chunk_id, mmr_score DESC
    ) ranked;

    -- Return results
    RETURN QUERY
    SELECT 
        (j->>'chunk_id')::UUID,
        (j->>'text')::TEXT,
        (j->>'section')::TEXT,
        COALESCE((j->>'timestamp_start')::FLOAT, 0),
        COALESCE((j->>'timestamp_end')::FLOAT, 0),
        (j->>'similarity')::FLOAT,
        COALESCE((j->>'mmr_score')::FLOAT, 0)
    FROM jsonb_array_elements(COALESCE(v_result, '[]'::jsonb)) j;
END;
$$ LANGUAGE plpgsql STABLE;
