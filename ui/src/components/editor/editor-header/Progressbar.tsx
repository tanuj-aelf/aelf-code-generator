import { useEffect, useRef, useState } from "react";
import "./style.css";

interface ComponentProps {
  isProcessCompleted: boolean;
}

const ProgressBar: React.FC<ComponentProps> = ({ isProcessCompleted }) => {
  const [percentage, setPercentage] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const clearProgressInterval = () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };

    if (isProcessCompleted) {
      clearProgressInterval();
      setPercentage(100);
      return;
    }

    intervalRef.current = setInterval(() => {
      setPercentage((prev) => {
        if (prev >= 98) {
          clearProgressInterval();
          return prev;
        }
        return prev > 70 ? prev + 0.1 : prev + 0.5;
      });
    }, 30);

    return () => {
      clearProgressInterval();
      setPercentage(0);
    };
  }, [isProcessCompleted]);

  return (
    <div className="progress">
      <div className="progress-value" style={{ width: `${percentage}%` }} />
    </div>
  );
};

export default ProgressBar;
