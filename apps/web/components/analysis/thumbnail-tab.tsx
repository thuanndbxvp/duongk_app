import { OutputCard } from './output-card';

interface Props {
  outputs: {
    output_14_thumbnail: any;
  };
}

export function ThumbnailTab({ outputs }: Props) {
  return (
    <div className="space-y-4">
      <OutputCard
        number={14}
        title="Thumbnail Analysis"
        description="Phân tích thumbnail bằng GPT-4o Vision"
        data={outputs?.output_14_thumbnail}
        cost={0.10}
      />
    </div>
  );
}
