// web-app/frontend/src/components/shared/ModulePanel.jsx
import React from 'react';

/**
 * 🔲 ModulePanel: Thành phần bọc (Wrapper Component) dùng chung cho toàn bộ hệ thống
 * @param {string} title - Tiêu đề của chức năng (Ví dụ: "Quản lý tiến trình")
 * @param {string} description - Mô tả ngắn gọn nhiệm vụ của tab
 * @param {React.ReactNode} actionButtons - Khu vực chứa nút bấm phụ nếu có (tùy chọn)
 * @param {React.ReactNode} children - LƯU Ý KỸ THUẬT: Đây là toàn bộ ruột giao diện của module con truyền vào
 */
function ModulePanel({ title, description, actionButtons, children }) {
  return (
    <div style={styles.panelContainer}>
      
      {/* 🔝 1. PHẦN ĐẦU TRUNG TÂM (HEADER) - Đồng bộ phong cách cho mọi module */}
      <div style={styles.panelHeader}>
        <div>
          <h3 style={styles.panelTitle}>{title}</h3>
          <p style={styles.panelDesc}>{description}</p>
        </div>
        
        {/* Nếu module con có truyền thêm các nút thao tác nhanh (như nút Làm mới, Xuất file), chúng sẽ hiện ở đây */}
        {actionButtons && (
          <div style={styles.actionArea}>
            {actionButtons}
          </div>
        )}
      </div>

      <hr style={styles.divider} />

      {/* 📥 2. PHẦN THÂN (BODY) - Nơi chứa "ruột" giao diện thực tế của từng Module */}
      <div style={styles.panelBody}>
        {children} 
      </div>
      
    </div>
  );
}

// 🎨 CẤU HÌNH CSS CHUẨN: Đảm bảo mọi module mở ra đều có giao diện đồng đều tuyệt đối
const styles = {
  panelContainer: {
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    border: '1px solid #e2e8f0',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    padding: '1.5rem',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    boxSizing: 'border-box'
  },
  panelHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
    gap: '1rem'
  },
  panelTitle: {
    margin: 0,
    fontSize: '1.25rem',
    fontWeight: '700',
    color: '#1e293b'
  },
  panelDesc: {
    margin: '0.25rem 0 0 0',
    fontSize: '0.875rem',
    color: '#64748b'
  },
  actionArea: {
    display: 'flex',
    gap: '0.5rem',
    alignItems: 'center'
  },
  divider: {
    border: 'none',
    borderTop: '1px solid #f1f5f9',
    margin: '0 0 1.5rem 0'
  },
  panelBody: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    minHeight: '0' // Kỹ thuật Flexbox ép phần thân không được tràn ra ngoài màn hình cha
  }
};

export default ModulePanel;