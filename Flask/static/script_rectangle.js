window.onload = function() {
    let canvas = document.getElementById('canvas');
    let ctx = canvas.getContext('2d');
    let img = new Image();
    let clickCount = 0;
    let rectStart = null;
    let rectEnd = null;
    let coordinates = []; 
    
    // Đường dẫn đến ảnh bạn muốn vẽ
    img.src = imagePath;  // Tải ảnh
    imageName1 = img.src.split('/').pop();
    imageFilename = imageName1.split('.')[0];

    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
    };

    // Lưu tọa độ khi nhấp chuột vào ảnh
    canvas.addEventListener('click', function(event) {
        let rect = canvas.getBoundingClientRect();
        let x = event.clientX - rect.left;
        let y = event.clientY - rect.top;
        clickCount++;
        if (clickCount === 1) {
            rectStart = { x: x, y: y };  // Điểm bắt đầu
            console.log("Start point:", rectStart);
        } else if (clickCount === 2) {
            rectEnd = { x: x, y: y };  // Điểm kết thúc
            console.log("End point:", rectEnd);
            // Vẽ hình chữ nhật từ điểm đầu đến điểm cuối
            let width = rectEnd.x - rectStart.x;
            let height = rectEnd.y - rectStart.y;
            ctx.drawImage(img, 0, 0);  // Vẽ lại hình ảnh
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            ctx.strokeRect(rectStart.x, rectStart.y, width, height);
            // Sau khi vẽ xong, reset clickCount để vẽ hình mới
            clickCount = 0;
        }
    });

    // Khi bấm nút save, gửi dữ liệu hình ảnh đến server
    document.getElementById('save').addEventListener('click', function() {
        let dataURL = canvas.toDataURL('image/png');
        fetch('/save-coordinates', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              x1: rectStart.x,
              y1: rectStart.y,
              x2: rectEnd.x,
              y2: rectEnd.y,
              imageName: imageFilename
            })
          })
          .then(response => response.json())
          .then(data => {
            alert('Tọa độ đã được lưu thành công!');
          })
          .catch(error => {
            console.error('Lỗi khi lưu tọa độ:', error);
          });
        });
    function addCoordinates(x1, y1, x2, y2) {
        coordinates.push({ x1, y1, x2, y2 });
    }
}