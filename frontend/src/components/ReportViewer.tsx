import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ReportViewerProps {
    content: string;
    title?: string;
    date?: string;
    className?: string;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({
    content,
    title,
    date,
    className = ''
}) => {
    // Split content by H2 headings to create sections
    const splitBySections = (content: string): string[] => {
        // Split by ## headings (H2)
        const sections = content.split(/(?=^## )/gm);
        return sections.filter(s => s.trim().length > 0);
    };

    const sections = splitBySections(content);

    return (
        <div className={`bg-white rounded-lg shadow-sm p-6 ${className}`}>
            {(title || date) && (
                <div className="mb-6 border-b pb-4">
                    {title && <h2 className="text-2xl font-bold text-gray-900">{title}</h2>}
                    {date && <p className="text-sm text-gray-500 mt-1">{date}</p>}
                </div>
            )}

            <div className="prose prose-blue max-w-none">
                <div className="columns-1 lg:columns-2 gap-6">
                    {sections.map((section, index) => (
                        <div key={index} className="break-inside-avoid mb-6">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    h1: ({ node, ...props }) => <h1 className="text-2xl font-bold mt-8 mb-4 border-b pb-2" {...props} />,
                                    h2: ({ node, ...props }) => <h2 className="text-xl font-bold mt-0 mb-3" {...props} />,
                                    h3: ({ node, ...props }) => <h3 className="text-lg font-semibold mt-4 mb-2" {...props} />,
                                    ul: ({ node, ...props }) => <ul className="list-disc list-inside space-y-1 my-4" {...props} />,
                                    ol: ({ node, ...props }) => <ol className="list-decimal list-inside space-y-1 my-4" {...props} />,
                                    li: ({ node, ...props }) => <li className="text-gray-700" {...props} />,
                                    p: ({ node, ...props }) => <p className="text-gray-700 leading-relaxed my-4" {...props} />,
                                    blockquote: ({ node, ...props }) => (
                                        <blockquote className="border-l-4 border-blue-200 pl-4 py-2 italic text-gray-600 bg-gray-50 rounded-r" {...props} />
                                    ),
                                    code: ({ node, ...props }) => {
                                        // @ts-ignore - inline property exists on props but TS might complain depending on version
                                        const { inline, className, children } = props;
                                        if (inline) {
                                            return <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono text-red-500" {...props} />;
                                        }
                                        return (
                                            <pre className="bg-gray-800 text-gray-100 p-4 rounded-lg overflow-x-auto my-4">
                                                <code className="font-mono text-sm" {...props} />
                                            </pre>
                                        )
                                    },
                                    table: ({ node, ...props }) => (
                                        <div className="overflow-x-auto my-6">
                                            <table className="min-w-full divide-y divide-gray-200 border" {...props} />
                                        </div>
                                    ),
                                    th: ({ node, ...props }) => <th className="px-4 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b" {...props} />,
                                    td: ({ node, ...props }) => <td className="px-4 py-2 border-b text-sm text-gray-700" {...props} />,
                                    a: ({ node, ...props }) => <a className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer" {...props} />,
                                }}
                            >
                                {section}
                            </ReactMarkdown>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
