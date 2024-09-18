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
    let startX, startY, endX, endY;

    canvas.addEventListener('mousedown', (event) => {
        if (!isDrawing) {
            isDrawing = true;
            startX = event.clientX - canvas.offsetLeft;
            startY = event.clientY - canvas.offsetTop;
        }
    });

    canvas.addEventListener('mousemove', (event) => {
        if (isDrawing) {
            endX = event.clientX - canvas.offsetLeft;
            endY = event.clientY - canvas.offsetTop;

            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.strokeRect(startX, startY, endX - startX, endY - startY);
        }
    });

    canvas.addEventListener('mouseup', () => {
        isDrawing = false;
    });
};
