export default function ConfirmDialog({ isOpen, title, message, confirmText = 'Confirm', cancelText = 'Cancel', onConfirm, onCancel, isDangerous = false }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay open" style={{ zIndex: 400 }}>
      <div className="confirm-dialog">
        <div className="confirm-dialog-header">
          <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text)' }}>{title}</h2>
        </div>
        <div className="confirm-dialog-body">
          <p style={{ fontSize: '14px', color: 'var(--text)', lineHeight: '1.6' }}>{message}</p>
        </div>
        <div className="confirm-dialog-footer">
          <button onClick={onCancel} className="confirm-btn-cancel">
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`confirm-btn-confirm ${isDangerous ? 'dangerous' : ''}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
