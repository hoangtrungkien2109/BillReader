window.onload = function() {
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    let isDrawing = false;
    let rectStart = null;
    let coordinates = [];
  
    // Đường dẫn đến ảnh
    img.src = imagePath;  // Tải ảnh
    imageName1 = img.src.split('/').pop();
    imageFilename = imageName1.split('.')[0]; // Thay thế bằng đường dẫn ảnh của bạn
  
    img.onload = function() {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
    };
  
    // Bắt đầu vẽ
    canvas.addEventListener('mousedown', (event) => {
      isDrawing = true;
      rectStart = { x: event.clientX - canvas.offsetLeft, y: event.clientY - canvas.offsetTop };
    });
  
    // Vẽ khi di chuyển chuột
    canvas.addEventListener('mousemove', (event) => {
      if (!isDrawing) return;
      const rect = {
        x: event.clientX - canvas.offsetLeft,
        y: event.clientY - canvas.offsetTop
      };
      redraw(); // Vẽ lại tất cả các hình trước khi vẽ hình mới
      ctx.strokeStyle = 'red'; // Thay đổi màu nếu cần
      ctx.strokeRect(rectStart.x, rectStart.y, rect.x - rectStart.x, rect.y - rectStart.y);
    });
  
    // Kết thúc vẽ
    canvas.addEventListener('mouseup', () => {
      isDrawing = false;
      if (rectStart) {
        coordinates.push({
          x1: rectStart.x,
          y1: rectStart.y,
          x2: rect.x,
          y2: rect.y,
          color: 'red' // Màu mặc định, có thể thay đổi
        });
        rectStart = null;
      }
    });
  
    // Vẽ lại tất cả các hình
    function redraw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
      coordinates.forEach(rect => {
        ctx.strokeStyle = rect.color;
        ctx.strokeRect(rect.x1, rect.y1, rect.x2 - rect.x1, rect.y2 - rect.y1);
      });
    }
    document.getElementById('save').addEventListener('click', async function() {
        try {
          const dataURL = canvas.toDataURL('image/png');
          const coordinatesData = JSON.stringify({ coordinates, imageName: imageFilename });
      
          const response = await fetch('/save-coordinates-test', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: coordinatesData
          });
      
          if (!response.ok) {
            throw new Error(`Error saving coordinates: ${response.status}`);
          }
      
          const data = await response.json();
          alert('Tọa độ đã được lưu thành công!');
        } catch (error) {
          console.error('Lỗi khi lưu tọa độ:', error);
          alert('Đã xảy ra lỗi khi lưu tọa độ.');
        }
      });
};
