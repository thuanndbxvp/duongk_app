import { OutputCard } from './output-card';

interface Props {
  outputs: {
    output_5_consistency: any;
    output_6_pacing: any;
    output_7_sentiment: any;
  };
}

export function NLPTab({ outputs }: Props) {
  return (
    <div className="space-y-4">
      <OutputCard
        number={5}
        title="Consistency Score (A5)"
        description="Độ nhất quán của kênh (0-100)"
        data={outputs?.output_5_consistency}
      />
      <OutputCard
        number={6}
        title="Pacing Profile"
        description="WPM (words per minute) và độ dài câu"
        data={outputs?.output_6_pacing}
      />
      <OutputCard
        number={7}
        title="Sentiment Distribution"
        description="Phân bố sentiment (positive/neutral/negative)"
        data={outputs?.output_7_sentiment}
      />
    </div>
  );
}
