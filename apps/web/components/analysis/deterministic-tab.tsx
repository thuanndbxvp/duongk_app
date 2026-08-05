import { OutputCard } from './output-card';

interface Props {
  outputs: {
    output_1_metadata: any;
    output_2_tags: any;
    output_3_performance: any;
    output_4_optimal_duration: any;
  };
}

export function DeterministicTab({ outputs }: Props) {
  return (
    <div className="space-y-4">
      <OutputCard
        number={1}
        title="Metadata Analysis"
        description="Thống kê tổng quan về videos"
        data={outputs?.output_1_metadata}
      />
      <OutputCard
        number={2}
        title="Tags Analysis"
        description="Phân tích tags và co-occurrence"
        data={outputs?.output_2_tags}
      />
      <OutputCard
        number={3}
        title="Performance Reports"
        description="Best/worst videos + Consistency Score (A5)"
        data={outputs?.output_3_performance}
      />
      <OutputCard
        number={4}
        title="Optimal Duration (A4)"
        description="Độ dài video tối ưu dựa trên engagement"
        data={outputs?.output_4_optimal_duration}
      />
    </div>
  );
}
