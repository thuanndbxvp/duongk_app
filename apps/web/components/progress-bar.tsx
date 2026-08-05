export function ProgressBar({ progress, barColor = 'bg-blue-600', height = 'h-3', bgColor = 'bg-gray-200' }: { progress: number, barColor?: string, height?: string, bgColor?: string }) {
  return (
    <div className={`w-full ${bgColor} rounded-full overflow-hidden ${height}`}>
      <div
        className={`${barColor} ${height} rounded-full transition-all duration-500 ease-out`}
        style={{ width: `${progress}%` }}
      />
    </div>
  );
}
