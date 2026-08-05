import { OutputCard } from './output-card';

interface Props {
  outputs: {
    output_12_insights: any;
    output_13_ideas: any;
  };
}

export function InsightsTab({ outputs }: Props) {
  return (
    <div className="space-y-4">
      <OutputCard
        number={12}
        title="Hidden Insights"
        description="Phát hiện ẩn (Chi-square + LLM narrate)"
        data={outputs?.output_12_insights}
        cost={0.05}
      />
      <OutputCard
        number={13}
        title="Idea Opportunities (A14)"
        description="Untapped opportunities (Gap Score)"
        data={outputs?.output_13_ideas}
      />
    </div>
  );
}
