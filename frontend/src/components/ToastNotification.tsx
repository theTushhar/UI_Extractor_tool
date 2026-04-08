import { useEffect } from "react";
import { CheckCircle, Copy } from "lucide-react";

interface Props {
  message: string;
  onDismiss: () => void;
}

export function ToastNotification({ message, onDismiss }: Props) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 2500);
    return () => clearTimeout(t);
  }, [onDismiss]);

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-slide-up">
      <div className="flex items-center gap-3 px-4 py-3 rounded-xl glass border border-mode-input/30 shadow-lg shadow-black/40">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-mode-input/15">
          <CheckCircle size={16} className="text-mode-input" />
        </div>
        <span className="text-sm font-medium text-slate-200">{message}</span>
        <Copy size={14} className="text-slate-500 ml-1" />
      </div>
    </div>
  );
}
