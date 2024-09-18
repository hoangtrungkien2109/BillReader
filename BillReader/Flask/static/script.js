window.onload = function() {
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');

    const image = new Image();
    image.src = imagePath;  // Sử dụng biến imagePath từ Flask để tải đúng ảnh

    image.onload = function() {
        canvas.width = image.width;
        canvas.height = image.height;
        ctx.drawImage(image, 0, 0, image.width, image.height);

        let drawing = false;

        canvas.addEventListener('mousedown', function() {
            drawing = true;
        });

        canvas.addEventListener('mouseup', function() {
            drawing = false;
            ctx.beginPath();
        });

        canvas.addEventListener('mousemove', function(event) {
            if (!drawing) return;
            const rect = canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;

            ctx.lineWidth = 3;
            ctx.lineCap = 'round';
            ctx.strokeStyle = 'red';

            ctx.lineTo(x, y);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(x, y);
        });

        document.getElementById('save').addEventListener('click', function() {
            const link = document.createElement('a');
            link.download = 'edited_image.png';
            link.href = canvas.toDataURL();
            link.click();
        });
    }
};
