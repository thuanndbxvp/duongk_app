// Auto-generated from OpenAPI schema
// Do not edit manually

export interface OpenAPISchema {
  // Schema: ChannelCollectionRequest
  export interface ChannelCollectionRequest {
    channel_id: string;
    max_videos?: number;
  }

  // Schema: ChannelCollectionResponse
  export interface ChannelCollectionResponse {
    channel_id: string;
    total_videos_collected: number;
    quality_videos_count: number;
    viral_videos_count: number;
    quality_videos: unknown[];
    viral_videos: unknown[];
  }

  // Schema: HTTPValidationError
  export interface HTTPValidationError {
    detail?: unknown[];
  }

  // Schema: NicheValidationRequest
  export interface NicheValidationRequest {
    keyword: string;
    user_id?: string;
    use_cache?: boolean;
  }

  // Schema: NicheValidationResponse
  export interface NicheValidationResponse {
    keyword: string;
    total_monthly_views: number;
    total_channels: number;
    avg_views_per_video: number;
    google_trends_interest: number;
    is_viable: boolean;
    suggested_titles: unknown[];
  }

  // Schema: TranscriptRequest
  export interface TranscriptRequest {
    video_id: string;
    languages?: unknown[];
  }

  // Schema: TranscriptResponse
  export interface TranscriptResponse {
    video_id: string;
    transcript: string;
    language: string;
    tier_used: number;
    cached: boolean;
  }

  // Schema: ValidationError
  export interface ValidationError {
    loc: unknown[];
    msg: string;
    type: string;
  }

  // Schema: VideoMetadata
  export interface VideoMetadata {
    video_id: string;
    title?: string;
    views?: number;
    likes?: number;
    comments?: number;
    duration_seconds?: number;
    published_at?: string;
  }

  // Schema: apps__api__modules__module_1__schemas__HealthResponse
  export interface apps__api__modules__module_1__schemas__HealthResponse {
    status: string;
    module: string;
    version: string;
  }

  // Schema: apps__api__modules__module_2a__schemas__HealthResponse
  export interface apps__api__modules__module_2a__schemas__HealthResponse {
    status: string;
    module: string;
    version: string;
  }

  // Schema: apps__api__modules__transcript__routes__HealthResponse
  export interface apps__api__modules__transcript__routes__HealthResponse {
    status: string;
    module: string;
    version: string;
  }

}