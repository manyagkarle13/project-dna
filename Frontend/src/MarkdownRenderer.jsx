import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/atom-one-dark.css';
import './MarkdownRenderer.css';

export default function MarkdownRenderer({ content }) {
  return (
    <ReactMarkdown
      rehypePlugins={[rehypeHighlight]}
      components={{
        h1: ({ node, ...props }) => <h1 style={{ fontSize: '24px', fontWeight: 700, marginTop: '16px', marginBottom: '12px' }} {...props} />,
        h2: ({ node, ...props }) => <h2 style={{ fontSize: '20px', fontWeight: 700, marginTop: '14px', marginBottom: '10px' }} {...props} />,
        h3: ({ node, ...props }) => <h3 style={{ fontSize: '16px', fontWeight: 600, marginTop: '12px', marginBottom: '8px' }} {...props} />,
        h4: ({ node, ...props }) => <h4 style={{ fontSize: '14px', fontWeight: 600, marginTop: '10px', marginBottom: '6px' }} {...props} />,
        p: ({ node, ...props }) => <p style={{ marginBottom: '12px', lineHeight: '1.6' }} {...props} />,
        ul: ({ node, ...props }) => <ul style={{ marginLeft: '20px', marginBottom: '12px', listStyle: 'disc' }} {...props} />,
        ol: ({ node, ...props }) => <ol style={{ marginLeft: '20px', marginBottom: '12px', listStyle: 'decimal' }} {...props} />,
        li: ({ node, ...props }) => <li style={{ marginBottom: '4px', lineHeight: '1.6' }} {...props} />,
        code: ({ node, inline, className, children, ...props }) => {
          if (inline) {
            return (
              <code style={{ background: 'rgba(0,0,0,0.1)', padding: '2px 6px', borderRadius: '3px', fontFamily: 'monospace', fontSize: '13px' }} {...props}>
                {children}
              </code>
            );
          }
          return null;
        },
        pre: ({ node, children, ...props }) => (
          <pre style={{
            background: 'rgba(0,0,0,0.05)',
            padding: '12px',
            borderRadius: '8px',
            overflow: 'auto',
            marginBottom: '12px',
            fontSize: '13px',
            lineHeight: '1.5',
            border: '1px solid rgba(0,0,0,0.1)',
            fontFamily: 'monospace'
          }} {...props}>
            {children}
          </pre>
        ),
        blockquote: ({ node, ...props }) => (
          <blockquote style={{
            borderLeft: '3px solid var(--accent)',
            paddingLeft: '12px',
            marginLeft: '0',
            marginBottom: '12px',
            color: 'var(--text-muted)',
            fontStyle: 'italic'
          }} {...props} />
        ),
        a: ({ node, ...props }) => (
          <a style={{ color: 'var(--accent)', textDecoration: 'underline', cursor: 'pointer' }} {...props} />
        ),
        strong: ({ node, ...props }) => <strong style={{ fontWeight: 600 }} {...props} />,
        em: ({ node, ...props }) => <em style={{ fontStyle: 'italic' }} {...props} />,
        table: ({ node, ...props }) => (
          <table style={{
            borderCollapse: 'collapse',
            width: '100%',
            marginBottom: '12px',
            border: '1px solid var(--border)'
          }} {...props} />
        ),
        th: ({ node, ...props }) => (
          <th style={{
            padding: '8px',
            textAlign: 'left',
            borderBottom: '2px solid var(--border)',
            fontWeight: 600,
            background: 'var(--bg-alt)'
          }} {...props} />
        ),
        td: ({ node, ...props }) => (
          <td style={{
            padding: '8px',
            borderBottom: '1px solid var(--border)'
          }} {...props} />
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
