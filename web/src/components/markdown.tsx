import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { CodeBlock } from "./code-block";

export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose-onefold">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Step content uses h2 and below; the page owns the single h1.
          h1: ({ children: text }) => <h2>{text}</h2>,
          a: ({ href, children: text }) => (
            <a href={href} target="_blank" rel="noreferrer noopener">
              {text}
            </a>
          ),
          pre: ({ children: code }) => <CodeBlock>{code}</CodeBlock>,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
