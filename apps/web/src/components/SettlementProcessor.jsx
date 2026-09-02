/**
 * Settlement Processing Frontend Component
 * REAL FORMWISE INTEGRATION - No mock OCR
 * 
 * Actual workflow:
 * 1. User uploads settlement PDF via FormWise document API
 * 2. Document stored in FormWise storage
 * 3. Trigger FormWise OCR processing (PaddleOCR)
 * 4. Retrieve OCR text from FormWise storage
 * 5. Pass real OCR text to settlement extraction API
 * 6. Process deductions, verification, evidence matching
 * 7. AI investigation for unresolved cases
 * 8. Generate decision
 * 9. Display results with audit trail
 */

import React, { useState } from 'react';

const SettlementProcessor = () => {
  const [state, setState] = useState({
    step: 'upload', // upload | ocr_processing | processing | results
    settlementDoc: null,
    settlementDocId: null,
    evidenceDocs: [],
    evidenceDocIds: [],
    results: null,
    error: null,
    loading: false,
    ocrStatus: null,
  });

  // REAL: Step 1 - Upload settlement PDF via FormWise API
  const handleSettlementUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      // Step 1a: Create upload intent
      const intentResponse = await fetch('/documents/upload-intents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          original_filename: file.name,
          content_type: file.type,
          file_size: file.size,
        }),
      });

      if (!intentResponse.ok) throw new Error('Failed to create upload intent');
      const { document_id: docId, upload_url } = await intentResponse.json();

      // Step 1b: Upload file to FormWise storage
      await fetch(upload_url, {
        method: 'PUT',
        headers: { 'Content-Type': file.type },
        body: file,
      });

      // Step 1c: Mark upload complete
      const completeResponse = await fetch(`/documents/${docId}/complete`, {
        method: 'POST',
      });

      if (!completeResponse.ok) throw new Error('Failed to complete upload');

      setState(prev => ({
        ...prev,
        settlementDoc: file,
        settlementDocId: docId,
        loading: false,
        ocrStatus: 'uploaded',
      }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        error: `Upload failed: ${err.message}`,
        loading: false,
      }));
    }
  };

  // REAL: Step 2 - Trigger FormWise OCR and wait for completion
  const triggerOCR = async () => {
    if (!state.settlementDocId) {
      setState(prev => ({ ...prev, error: 'No document to process' }));
      return;
    }

    setState(prev => ({ 
      ...prev, 
      loading: true, 
      ocrStatus: 'processing',
      step: 'ocr_processing'
    }));

    try {
      // Trigger OCR
      const ocrStartResponse = await fetch(`/documents/${state.settlementDocId}/ocr`, {
        method: 'POST',
      });

      if (!ocrStartResponse.ok) throw new Error('Failed to start OCR');

      // Poll for OCR completion
      let ocrText = null;
      let attempts = 0;
      const maxAttempts = 60; // 5 minutes with 5-second intervals

      while (!ocrText && attempts < maxAttempts) {
        await new Promise(r => setTimeout(r, 5000)); // Wait 5 seconds
        attempts++;

        const ocrStatusResponse = await fetch(`/documents/${state.settlementDocId}/ocr`);
        const ocrData = await ocrStatusResponse.json();

        if (ocrData.status === 'completed') {
          ocrText = ocrData.extracted_text;
          setState(prev => ({ ...prev, ocrStatus: 'completed' }));
        } else if (ocrData.status === 'failed') {
          throw new Error('OCR processing failed');
        }
      }

      if (!ocrText) throw new Error('OCR processing timeout');

      // Proceed to settlement processing
      await processSettlement(ocrText);
    } catch (err) {
      setState(prev => ({
        ...prev,
        error: `OCR failed: ${err.message}`,
        loading: false,
        ocrStatus: 'failed',
      }));
    }
  };

  // REAL: Step 3 - Process settlement with real OCR text
  const processSettlement = async (ocrText) => {
    setState(prev => ({ 
      ...prev, 
      loading: true, 
      step: 'processing',
      ocrStatus: null
    }));

    try {
      // Call real settlement processing API with actual OCR text
      const response = await fetch('/v1/settlements/process-document', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          documentId: state.settlementDocId,
          ocrText: ocrText, // REAL OCR text from FormWise
          evidenceDocumentIds: state.evidenceDocIds,
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Processing failed: ${error}`);
      }

      const results = await response.json();
      setState(prev => ({
        ...prev,
        results,
        step: 'results',
        loading: false,
      }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        error: err.message,
        loading: false,
        step: 'upload',
      }));
    }
  };

  // REAL: Upload evidence documents via FormWise API
  const handleEvidenceUpload = async (event) => {
    const files = event.target.files;
    if (!files) return;

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const newEvidenceIds = [];

      for (const file of Array.from(files)) {
        // Create upload intent
        const intentResponse = await fetch('/documents/upload-intents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            original_filename: file.name,
            content_type: file.type,
            file_size: file.size,
          }),
        });

        if (!intentResponse.ok) continue;

        const { document_id: docId, upload_url } = await intentResponse.json();

        // Upload file
        await fetch(upload_url, {
          method: 'PUT',
          headers: { 'Content-Type': file.type },
          body: file,
        });

        // Complete upload
        await fetch(`/documents/${docId}/complete`, { method: 'POST' });

        newEvidenceIds.push(docId);
      }

      setState(prev => ({
        ...prev,
        evidenceDocs: [...prev.evidenceDocs, ...Array.from(files)],
        evidenceDocIds: [...prev.evidenceDocIds, ...newEvidenceIds],
        loading: false,
      }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        error: `Evidence upload failed: ${err.message}`,
        loading: false,
      }));
    }
  };

  const handleRemoveEvidence = (index) => {
    setState(prev => ({
      ...prev,
      evidenceDocs: prev.evidenceDocs.filter((_, i) => i !== index),
      evidenceDocIds: prev.evidenceDocIds.filter((_, i) => i !== index),
    }));
  };

  // Render upload step
  if (state.step === 'upload') {
    return (
      <div style={{ maxWidth: '600px', margin: '0 auto', padding: '20px' }}>
        <h1>Settlement Processor</h1>
        <p>Upload a settlement PDF to begin processing</p>

        <div style={{ marginBottom: '20px' }}>
          <h3>Settlement Document</h3>
          <input
            type="file"
            accept=".pdf"
            onChange={handleSettlementUpload}
            disabled={state.loading}
          />
          {state.settlementDoc && (
            <p>Selected: {state.settlementDoc.name}</p>
          )}
        </div>

        <div style={{ marginBottom: '20px' }}>
          <h3>Evidence Documents (Optional)</h3>
          <input
            type="file"
            multiple
            onChange={handleEvidenceUpload}
            disabled={state.loading || !state.settlementDocId}
          />
          {state.evidenceDocs.length > 0 && (
            <ul>
              {state.evidenceDocs.map((doc, i) => (
                <li key={i}>
                  {doc.name}
                  <button onClick={() => handleRemoveEvidence(i)}>Remove</button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {state.settlementDocId && (
          <button
            onClick={triggerOCR}
            disabled={state.loading}
            style={{
              padding: '10px 20px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: state.loading ? 'not-allowed' : 'pointer',
            }}
          >
            {state.loading ? 'Processing...' : 'Process Settlement'}
          </button>
        )}

        {state.error && (
          <div style={{ color: 'red', marginTop: '20px' }}>
            Error: {state.error}
          </div>
        )}
      </div>
    );
  }

  // Render OCR processing step
  if (state.step === 'ocr_processing') {
    return (
      <div style={{ maxWidth: '600px', margin: '0 auto', padding: '20px' }}>
        <h1>Processing OCR</h1>
        <p>Status: {state.ocrStatus}</p>
        <p>Extracting text from PDF using FormWise OCR (PaddleOCR)...</p>
        {state.error && (
          <div style={{ color: 'red' }}>Error: {state.error}</div>
        )}
      </div>
    );
  }

  // Render results step
  if (state.step === 'results') {
    const r = state.results;
    return (
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '20px' }}>
        <h1>Settlement Processing Results</h1>

        {r.settlement_id && (
          <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
            <h3>Settlement #{r.settlement_id}</h3>
            <p>Status: <strong>{r.status}</strong></p>
            <p>Gross Amount: {r.gross_amount}</p>
            <p>Net Amount: {r.net_amount}</p>
          </div>
        )}

        {r.deductions && r.deductions.length > 0 && (
          <div style={{ marginBottom: '20px' }}>
            <h3>Deductions</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #ccc' }}>
                  <th style={{ textAlign: 'left', padding: '10px' }}>Type</th>
                  <th style={{ textAlign: 'left', padding: '10px' }}>Amount</th>
                  <th style={{ textAlign: 'left', padding: '10px' }}>Confidence</th>
                  <th style={{ textAlign: 'left', padding: '10px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {r.deductions.map((d, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '10px' }}>{d.deduction_type}</td>
                    <td style={{ padding: '10px' }}>{d.amount}</td>
                    <td style={{ padding: '10px' }}>{(d.extracted_with_confidence * 100).toFixed(0)}%</td>
                    <td style={{ padding: '10px' }}>{d.verification_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {r.decision && (
          <div style={{
            padding: '15px',
            backgroundColor: r.decision.status === 'approved' ? '#d4edda' : '#fff3cd',
            border: '1px solid #ccc',
            borderRadius: '4px',
            marginBottom: '20px'
          }}>
            <h3>Final Decision</h3>
            <p><strong>Status:</strong> {r.decision.status.toUpperCase()}</p>
            <p><strong>Confidence:</strong> {(r.decision.confidence * 100).toFixed(0)}%</p>
            <p><strong>Explanation:</strong> {r.decision.explanation}</p>
          </div>
        )}

        <button
          onClick={() => setState(prev => ({ ...prev, step: 'upload', results: null }))}
          style={{
            padding: '10px 20px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Process Another Settlement
        </button>
      </div>
    );
  }

  return null;
};

export default SettlementProcessor;
