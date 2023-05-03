import React, { useRef, useEffect } from 'react';

const DaqConfigModuleList = ({ jsonInput }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // Scale canvas to fit screen
    const scale = window.devicePixelRatio;
    const canvasWidth = canvas.offsetWidth;
    const canvasHeight = canvas.offsetHeight;
    canvas.width = canvasWidth * scale;
    canvas.height = canvasHeight * scale;
    ctx.scale(scale, scale);

    // Draw rectangles based on JSON input
    for (const key in jsonInput) {
      const [startX, startY, endX, endY] = jsonInput[key];
      ctx.fillStyle = 'red';
      ctx.fillRect(startX, startY, endX - startX, endY - startY);
      ctx.fillStyle = 'white';
      ctx.font = '30px Arial';
      const textWidth = ctx.measureText(key).width;
      const textHeight = 30;
      const textX = startX + (endX - startX - textWidth) / 2;
      const textY = startY + (endY - startY + textHeight) / 2;
      ctx.fillText(key, textX, textY);
    }
  }, [jsonInput]);

  const handleCanvasClick = () => {
    const canvas = canvasRef.current;
    const newCanvas = document.createElement('canvas');
    newCanvas.width = 2016;
    newCanvas.height = 2016;
    const newCtx = newCanvas.getContext('2d');
    newCtx.drawImage(canvas, 0, 0, 2016, 2016);
    const dataURL = newCanvas.toDataURL('image/png');
    const newWindow = window.open();
    newWindow.document.write(`<img src="${dataURL}" alt="unscaled canvas"/>`);
    newWindow.document.title = 'Unscaled Canvas';
  };

  return (
    <canvas
      ref={canvasRef}
      style={{ width: '100%', height: '100%', border: '1px solid black' }}
      onClick={handleCanvasClick}
    />
  );
};

export default DaqConfigModuleList;
