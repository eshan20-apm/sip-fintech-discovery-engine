import React, { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';

export default function BiasBanner() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="bias-banner">
      <div className="bias-banner-content">
        <AlertTriangle className="bias-icon" size={18} />
        <div>
          <span className="bias-strong">Research Complainant Bias Caution:</span>{' '}
          Public reviews and forum discussions disproportionately capture vocal dissatisfaction and operational friction points. Frequency of complaints does not equal statistical population-wide prevalence.
        </div>
      </div>
      <button 
        onClick={() => setDismissed(true)} 
        className="btn-close"
        title="Dismiss warning"
      >
        <X size={16} />
      </button>
    </div>
  );
}
