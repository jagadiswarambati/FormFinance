import type { StructuredDocument } from '@/services/documents/upload-api';

export function StructuredDocumentViewer({ document }: { document: StructuredDocument }) {
  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
        <p className="text-sm text-slate-500">Document type</p>
        <h2 className="mt-1 text-xl font-semibold">{document.documentType.replaceAll('_', ' ')}</h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Understanding confidence: {Math.round(document.confidenceSummary.overall * 100)}%
        </p>
      </section>
      <section>
        <h2 className="text-lg font-semibold">Sections and fields</h2>
        {document.sections.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">No sections were detected.</p>
        ) : (
          <div className="mt-3 space-y-4">
            {document.sections.map((section) => (
              <article
                key={section.id}
                className="rounded-xl border border-slate-200 p-4 dark:border-slate-800"
              >
                <h3 className="font-medium">{section.title}</h3>
                <ul className="mt-3 space-y-2 text-sm">
                  {document.fields
                    .filter((field) => field.sectionId === section.id)
                    .map((field) => (
                      <li key={field.id} className="flex flex-wrap justify-between gap-2">
                        <span>
                          {field.label}
                          {field.required ? ' *' : ''}
                        </span>
                        <span className="text-slate-600 dark:text-slate-300">
                          {field.normalizedValue ?? field.value ?? 'Missing'}
                        </span>
                      </li>
                    ))}
                </ul>
              </article>
            ))}
          </div>
        )}
      </section>
      {document.tables.map((table) => (
        <section key={table.id}>
          <h2 className="text-lg font-semibold">Table</h2>
          <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-900">
                <tr>
                  {table.headers.map((header) => (
                    <th key={header} className="px-3 py-2 font-medium">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((row, index) => (
                  <tr key={index} className="border-t border-slate-200 dark:border-slate-800">
                    {row.map((cell, cellIndex) => (
                      <td key={cellIndex} className="px-3 py-2">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
      <section className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 p-4 dark:border-slate-800">
          <h2 className="font-semibold">Checkboxes</h2>
          {document.checkboxes.length ? (
            <ul className="mt-2 text-sm">
              {document.checkboxes.map((item) => (
                <li key={item.id}>
                  {item.label}: {item.state}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-slate-500">None detected.</p>
          )}
        </div>
        <div className="rounded-xl border border-slate-200 p-4 dark:border-slate-800">
          <h2 className="font-semibold">Review needed</h2>
          <p className="mt-2 text-sm">Signature: {document.signatureStatus}</p>
          {document.missingFields.map((field) => (
            <p key={field.fieldId} className="mt-1 text-sm">
              {field.label}: {field.certainty.replaceAll('_', ' ')}
            </p>
          ))}
        </div>
      </section>
    </div>
  );
}
