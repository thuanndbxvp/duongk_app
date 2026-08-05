import { OutputCard } from './output-card';

interface Props {
  outputs: {
    output_8_hook: any;
    output_9_structure: any;
    output_10_emotion: any;
    output_11_mimic_rules: any;
  };
}

export function LLMTab({ outputs }: Props) {
  return (
    <div className="space-y-4">
      <OutputCard
        number={8}
        title="Hook Analysis"
        description="Phân tích Hook patterns bằng GPT-4o"
        data={outputs?.output_8_hook}
        cost={0.02}
      />
      <OutputCard
        number={9}
        title="Structural Formula"
        description="Công thức cấu trúc video"
        data={outputs?.output_9_structure}
        cost={0.02}
      />
      <OutputCard
        number={10}
        title="Emotion Distribution"
        description="Phân bố cảm xúc (PhoBERT + j-hartmann)"
        data={outputs?.output_10_emotion}
      />
      <OutputCard
        number={11}
        title="Mimic Rules"
        description="Quy tắc bắt chước phong cách kênh"
        data={outputs?.output_11_mimic_rules}
        cost={0.02}
      />
    </div>
  );
}
