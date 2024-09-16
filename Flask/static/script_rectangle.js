window.onload = function() {
    let canvas = document.getElementById('canvas');
    let ctx = canvas.getContext('2d');
    let img = new Image();
    let clickCount = 0;
    let rectStart = null;
    let rectEnd = null;

    // Đường dẫn đến ảnh bạn muốn vẽ
    img.src = imagePath;  // Tải ảnh

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
        fetch('/save-drawed-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                imageData: dataURL,
                username: "username",
                imageName: "image_name"
            })
        })
        .then(response => response.json())
        .then(data => {
            alert('Image saved successfully!');
        })
        .catch(error => {
            console.error('Error saving image:', error);
        });
    });
}