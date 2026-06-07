import { Fragment } from "react";

/**
 * Render a backend-highlighted snippet safely.
 * Backend wraps matches in <mark>...</mark>; everything else is treated as plain text.
 */
export function Highlighted({ html }: { html: string }) {
  const parts = html.split(/(<mark>.*?<\/mark>)/g);
  return (
    <>
      {parts.map((part, i) => {
        const match = part.match(/^<mark>(.*?)<\/mark>$/);
        if (match) {
          return <mark key={i}>{match[1]}</mark>;
        }
        return <Fragment key={i}>{part}</Fragment>;
      })}
    </>
  );
}
