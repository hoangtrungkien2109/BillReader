window.onload = function() {
    let canvas = document.getElementById('canvas');
    let ctx = canvas.getContext('2d');
    let img = new Image();
    let clickCount = 0;
    let rectStart = null;
    let coordinates = [];  // Store all rectangle coordinates

    // Replace with your actual image path
    img.src = imagePath;  
    imageName1 = img.src.split('/').pop();
    imageFilename = imageName1.split('.')[0];

    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
    };

    // Function to redraw image and all rectangles
    function redrawAll() {
        ctx.drawImage(img, 0, 0);  // Redraw image
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 2;
        coordinates.forEach(function(coord) {
            let width = coord.x2 - coord.x1;
            let height = coord.y2 - coord.y1;
            ctx.strokeRect(coord.x1, coord.y1, width, height);  // Redraw rectangles
        });
    }

    // Save coordinates on click and draw the rectangle
    canvas.addEventListener('click', function(event) {
        let rect = canvas.getBoundingClientRect();
        let x = event.clientX - rect.left;
        let y = event.clientY - rect.top;
        clickCount++;

        if (clickCount === 1) {
            rectStart = { x: x, y: y };  // Start point
            console.log("Start point:", rectStart);
        } else if (clickCount === 2) {
            let rectEnd = { x: x, y: y };  // End point
            console.log("End point:", rectEnd);
            
            // Add new rectangle to coordinates array
            coordinates.push({
                x1: rectStart.x, 
                y1: rectStart.y, 
                x2: rectEnd.x, 
                y2: rectEnd.y
            });

            // Redraw the canvas with all rectangles
            redrawAll();

            // Reset clickCount for next rectangle
            clickCount = 0;
        }
    });

    // Send coordinates to the server when save button is clicked
    document.getElementById('save').addEventListener('click', function() {
        fetch('/save-coordinates-test', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              coordinates: coordinates,  // Send all rectangles
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
}

