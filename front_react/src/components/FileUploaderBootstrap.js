import React, { useRef, useState } from 'react';

const FileUploaderBootstrap = () => {
  const fileInputRef = useRef(null);
  const [fileName, setFileName] = useState('');
  const [status, setStatus] = useState('');

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setFileName(file.name);
    setStatus('Загрузка...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        setStatus('✅ Файл успешно отправлен!');
      } else {
        setStatus('❌ Ошибка при загрузке файла.');
      }
    } catch (error) {
      console.error('Ошибка:', error);
      setStatus('❌ Ошибка при отправке.');
    }
  };

  return (
    <div className="container mt-5 p-4 border rounded shadow-sm bg-light" style={{ maxWidth: '600px' }}>
      <h3 className="mb-4 text-center">Загрузка файла в БДКЕ</h3>
      <div className="text-center">
        <button
          className="btn btn-primary mb-3"
          onClick={() => fileInputRef.current.click()}
        >
          Выбрать Excel / CSV файл
        </button>
        <input
          type="file"
          accept=".csv, .xlsx, .xls"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <div className="text-muted mb-2">{fileName && `Выбран файл: ${fileName}`}</div>
        <div>{status && <div className="alert alert-info p-2">{status}</div>}</div>
      </div>
    </div>
  );
};

export default FileUploaderBootstrap;
