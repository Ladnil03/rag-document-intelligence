import { useId, useRef, useState, type FormEvent, type KeyboardEvent } from "react";

import { Button } from "@/components/ui/Button";

interface ChatInputProps {
  onSend: (text: string) => void;
  onCancel?: () => void;
  disabled?: boolean;
  sending?: boolean;
  placeholder?: string;
}

export const ChatInput = ({
  onSend,
  onCancel,
  disabled,
  sending,
  placeholder = "Ask a question about your documents...",
}: ChatInputProps) => {
  const [value, setValue] = useState("");
  const inputId = useId();
  const formId = useId();
  const ref = useRef<HTMLTextAreaElement>(null);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const text = value.trim();
    if (!text || disabled || sending) return;
    onSend(text);
    setValue("");
    // Restore focus so the user can immediately send a follow-up.
    requestAnimationFrame(() => ref.current?.focus());
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(e as unknown as FormEvent);
    }
  };

  return (
    <form
      id={formId}
      onSubmit={submit}
      className="flex items-end gap-2 border-t border-border bg-bg-panel/80 px-3 py-3"
    >
      <label htmlFor={inputId} className="sr-only">
        Message
      </label>
      <textarea
        ref={ref}
        id={inputId}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKey}
        placeholder={placeholder}
        rows={1}
        disabled={disabled}
        aria-label="Message"
        className="max-h-32 min-h-[40px] flex-1 resize-none rounded-md border border-border bg-bg-card px-3 py-2 text-sm text-ink placeholder:text-ink-subtle focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/40 disabled:opacity-60"
      />
      {sending ? (
        <Button type="button" variant="secondary" onClick={onCancel}>
          Stop
        </Button>
      ) : (
        <Button type="submit" disabled={disabled || !value.trim()}>
          Send
        </Button>
      )}
    </form>
  );
};
