
// a module to create a Floor Layout object

export class FloorPlan {
    showMousePos = false;

    evt;
    canvas;
    ctx;
    img;
    imgPin;
    imgPinGreen;
    imgPinYellow;

    // for pin mode
    addingPinMode = false;
    mouseDown = false;
    pinIsMoving = true;
    newPin = {
        x: 0,
        y: 0
    };
    pins = [{x: 40, y:60}, {x:100, y:200}];
    showingPins = true;
    highlightedPin = null;


    // for room mode
    addingRoomMode = false;
    startPoint = ''
    endPoint = ''
    newRoom = {
        name: '',
        x: 0,
        y: 0,
        width: 0,
        height: 0
    }
    rooms = [{name: 'hello', x:300, y:200, width: 100, height: 100}];
    showingRooms = true;

    // for fingerprinting Mode
    fingerprintingMode = false;
    showingRoutes = true;
    routes = [];
    routePoints = [];
    pointOffset = 30; // px // distance between route points. In reality, it is 50cm
    currentRoute = 0;
    currentRoutePoint = 0;
    nextRoutePoint = {
        x: 0,
        y: 0
    }

    // for Radio Map Mode
    radioMapMode = false;
    radioMap;

    // for testing Mode
    testingMode = false;
    selectedPoint = {};
    predPoints = [];
    predRooms = [];


    doNothing = false;

    constructor(canvas, img, imgPin, imgPinGreen, imgPinYellow) {
        let self = this;
        self.canvas = canvas;
        self.ctx = self.canvas.getContext("2d");
        self.img = img;
        self.imgPin = imgPin;
        self.imgPinGreen = imgPinGreen;
        self.imgPinYellow = imgPinYellow;

        self.redrawAll(self.evt)

        // add event listeners
        self.canvas.addEventListener('mousemove', function(evt) {
            self.evt = evt;
            self.redrawAll(evt);
        }, false);

        self.canvas.addEventListener('mousedown', function(evt) {
            if (self.doNothing) return;
            self.handleMouseDown(evt);
        })
        self.canvas.addEventListener('mouseup', function(evt) {
            if (self.doNothing) return;
            self.handleMouseUp(evt);
        })
    }


    // ---------------------------------------------- Setters ------------------------------------------------- //
    toggleShowingPins() {
        if (this.showingPins == true){
            this.showingPins = false
        } else {
            this.showingPins = true
        }
        this.redrawAll(this.evt);
    }

    toggleShowingRooms() {
        if (this.showingRooms == true){
            this.showingRooms = false
        } else {
            this.showingRooms = true
        }
        this.redrawAll(this.evt);
    }

    setMode(mode) {
        // console.log("Changing mode: ", mode)
        if (mode == 'pins') {
            this.addingPinMode = true;
            this.addingRoomMode = false;
            this.fingerprintingMode = false;
            this.radioMapMode = false;
            this.testingMode = false;

            this.showingRoutes = false;
            this.showingPins = true;
        } else if (mode == 'rooms') {
            this.addingPinMode = false;
            this.addingRoomMode = true;
            this.fingerprintingMode = false;
            this.radioMapMode = false;
            this.testingMode = false;

            this.showingRoutes = false;
            this.showingPins = false;
        } else if (mode == 'fingerprinting') {
            this.addingPinMode = false;
            this.addingRoomMode = false;
            this.fingerprintingMode = true;
            this.radioMapMode = false;
            this.testingMode = false;

            this.showingRoutes = true;
            this.showingPins = false;
        } else if (mode == 'radio_map') {
            this.addingPinMode = false;
            this.addingRoomMode = false;
            this.fingerprintingMode = false;
            this.radioMapMode = true;
            this.testingMode = false;

            this.showingRoutes = false;
            this.showingPins = false;
        } else if (mode == 'testing') {
            this.addingPinMode = false;
            this.addingRoomMode = false;
            this.fingerprintingMode = false;
            this.radioMapMode = false;
            this.testingMode = true;

            this.showingRoutes = false;
            this.showingPins = false;
        }
        this.redrawAll(this.evt)
    }

    setPins(pins) {
        this.pins = pins;
        this.redrawAll(this.evt);
    }

    setRooms(rooms) {
        this.rooms = rooms;
        this.redrawAll(this.evt);
    }

    setRoutes(routes) {
        this.routes = routes;
        this.redrawAll(this.evt);
    }

    setDoNothing(val) {
        this.doNothing = val;
        this.redrawAll(this.evt)
    }


    // ------------------------------------------------- Getters ----------------------------------------- //


    // -------------------------------------------------- Event Handlers ----------------------------------- //
    handleMouseDown(evt) {
        if (this.addingPinMode) {
            this.mouseDown = true;
            this.pinIsMoving = true;
            this.redrawAll(evt);

        } else if (this.addingRoomMode) { // other mode
            let mousePos = this.getMousePos(this.canvas, evt);
            this.startPoint = mousePos;

        } else if (this.fingerprintingMode) {
            let mousePos = this.getMousePos(this.canvas, evt);
            if (this.routePoints.length == 0) {
                this.routePoints.push(mousePos);
            } else {
                if (this.nextRoutePoint.x != 0 && this.nextRoutePoint.y != 0) {
                    let nextPoint = {...this.nextRoutePoint}
                    this.routePoints.push(nextPoint);
                    this.nextRoutePoint.x = 0;
                    this.nextRoutePoint.y = 0;
                }
            }
            // console.log(this.routePoints)
        }
    }

    handleMouseUp(evt) {
        if (this.addingPinMode) {
            if (this.mouseDown == true) {
                // console.log('Mouse was clicked')
                this.pinIsMoving = false; // stop moving the pin
                let mousePos = this.getMousePos(this.canvas, evt);
                // save pin location
                this.newPin = mousePos;
                this.redrawAll(evt);
            }
            this.mouseDown = false;

        } else if (this.addingRoomMode) { // other mode
            let mousePos = this.getMousePos(this.canvas, evt);
            this.endPoint = mousePos;
            this.newRoom = this.pointsToRect(this.startPoint.x, this.startPoint.y, this.endPoint.x, this.endPoint.y);
            this.startPoint = '';
            this.endPoint = '';
            const event = new Event('showNewRoomModal')
            evt.target.dispatchEvent(event)

        } else if (this.fingerprintingMode) {
            this.drawAllRoutes();
            this.nextRoutePoint.x = 0;
            this.nextRoutePoint.y = 0;
        }
    }

    // ---------------------------------------------  Drawing -------------------------------------------------- //
    changeSelectedTestPoint(test_point, point_preds, rooms) {

        console.log("Testing Point...:", test_point.room, test_point.x, test_point.y)
        let realPoint = {
            x: test_point.x,
            y: test_point.y
        }
        realPoint = this.scalePoint(realPoint, this.canvas.width, this.canvas.height);

        this.selectedPoint = realPoint;
        this.predPoints = point_preds;
        this.predRooms = rooms;
        this.drawTestResults();
    }

    drawTestResults() {
        if (!this.selectedPoint.x || this.predRooms.length == 0 || this.predPoints.length == 0) return;

        // clear old results
        this.testingMode = false; // only the testing mode was true!
        this.redrawAll();
        this.testingMode = true;

        this.drawPoint(this.selectedPoint, 'black', 5)
        // draw rooms
        this.predRooms.forEach((room,i) => {
            console.log(i, room)
        })
        let colors = ['red', 'green', 'blue', 'yellow', 'orange']
        // draw knns
        this.predPoints.forEach((point, i) => {
            let color = colors[i]
            let p = {
                x: point.x,
                y: point.y
            }
            p = this.scalePoint(p, this.canvas.width, this.canvas.height)
            console.log(i, point.room, p)
            this.drawPoint(p, color, 2)
        })
    }

    drawPoint(point, color, radius) {
        // draw point center
        this.ctx.beginPath();
        this.ctx.fillStyle = color;
        this.ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.stroke();
    }

    changeSelectedBSSID(bssid) {
        if (!bssid) return;
        this.selectedBSSID = bssid;
        // console.log("selected", bssid);
        // console.log("Radio map:", this.radioMap);

        this.drawRadioMapForBSSID();
    }

    drawRadioMapForBSSID() {
        if (!this.radioMap || !this.selectedBSSID) return;
        let numberOfPoints = Object.keys(this.radioMap['pointX']).length;

        for (let i=0; i<numberOfPoints; i++) {
            let rssi_value = this.radioMap[this.selectedBSSID][i];
            let level = this.dbmToQuality(rssi_value) / 100; // from 0 to 1
            let x = this.radioMap['pointX'][i];
            let y = this.radioMap['pointY'][i];
            let point = this.scalePoint({x,y}, this.canvas.width, this.canvas.height)


            // draw the rect
            let width = 25;
            this.ctx.beginPath();

            let red = Math.floor(255 * (1 - level));
            let green = Math.floor(255 * level);
            let blue = 0;

            if (level == 0) {
                red=0;
                red=0;

            }
            this.ctx.fillStyle = `rgb(${red},${green},${blue})`;
            this.ctx.rect(point.x-width/2, point.y - width/2, width, width);
            this.ctx.fill();
            this.ctx.stroke();
        }
    }

    drawAllPins() {
        let pins = this.pins;
        for (let i=0; i<pins.length; i++) {
            pins[i] = this.scalePoint(pins[i], this.canvas.width, this.canvas.height);
            if (i==0 || pins[i].x != pins[i-1].x || pins[i].y != pins[i-1].y) { // if x and y are different from the previous point
                this.ctx.drawImage(this.imgPin, pins[i].x - this.imgPin.width/2 +1, pins[i].y - this.imgPin.height, this.imgPin.width, this.imgPin.height);
            }
        }
        // this.pins.forEach(pin => {
        //     pin = this.scalePoint(pin, this.canvas.width, this.canvas.height);
        //     this.ctx.drawImage(this.imgPin, pin.x - this.imgPin.width/2 +1, pin.y - this.imgPin.height, this.imgPin.width, this.imgPin.height);
        // })
    }

    drawAllRooms() {
        this.rooms.forEach((room,i) => { // room(x,y,width,height)
            this.scalePoint(room, this.canvas.width, this.canvas.height); // scaling x,y of room
            let roomDims = { x: room.width, y: room.height }
            this.scalePoint(roomDims, this.canvas.width, this.canvas.height);
            room.width = roomDims.x;
            room.height = roomDims.y;

            // draw rect
            this.ctx.beginPath();
            this.ctx.rect(room.x, room.y, room.width, room.height);
            this.ctx.stroke();
            // draw index of rect
            this.ctx.font = '11pt Calibri';
            this.ctx.fillStyle = 'black';
            let text = (i) + '. ' + room.name;
            this.ctx.fillText(text, room.x+5, room.y+15);
        })
    }

    drawAllRoutes() {
        // paint the current route
        this.drawRoute(this.routePoints)

        // paint the previous routes
        this.routes.forEach((route, i) => {
            this.drawRoute(route, i)
        })
    }

    drawRoute(route, routeIndex) {
        let canvasW = this.canvas.width;
        let canvasH = this.canvas.height;

        if (routeIndex != undefined) {
            // console.log("Drawing route:", routeIndex);
            // draw index of route
            this.ctx.font = 'bold 11pt Calibri';
            this.ctx.fillStyle = 'black';
            let text = "r:" + routeIndex;
            this.ctx.fillText(text, route[0].x+5, route[0].y+15);
        }
        route.forEach((point, i) => {
            point = this.scalePoint(point, canvasW, canvasH);
            this.ctx.beginPath();
            let radius = 2;
            this.ctx.fillStyle = 'black';
            if (i == this.currentRoutePoint && routeIndex == this.currentRoute) {
                radius = 4;
                this.ctx.fillStyle = 'green';
            }
            this.ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.stroke();
            // draw index of point
            this.ctx.font = '7pt Calibri';
            this.ctx.fillStyle = 'black';
            this.ctx.fillText(i + '.', point.x-2, point.y-5);
        })
        // draw the lines between points
        for (let i=0; i<route.length -1; i++) {
            let point1 = this.scalePoint(route[i], canvasW, canvasH);
            let point2 = this.scalePoint(route[i+1], canvasW, canvasH);
            this.ctx.beginPath();
            this.ctx.moveTo(point1.x, point1.y);
            this.ctx.lineTo(point2.x, point2.y);
            this.ctx.strokeStyle = '#FFA500';
            this.ctx.stroke();
            this.ctx.strokeStyle = '#000000'; // change color back to default
        }
    }

    scalePoint(point, canvasW, canvasH) {
        point.x = point.x * canvasW <= canvasW? Math.floor(point.x * canvasW) : point.x; // if the coordinates are percentages, then multiply them by the width or height of the canvas else, just draw them as they are
        point.y = point.y * canvasH <= canvasH? Math.floor(point.y * canvasH) : point.y;
        return point
    }

    redrawAll(evt) {
        if (this.testingMode && this.predPoints.length!=0 && this.predRooms.length!==0) return;
        let new_img_width = this.canvas.width;
        let ratio = 600/this.img.width;
        let new_img_height = ratio * this.img.height
        this.ctx.drawImage(this.img, 0, 0, new_img_width, new_img_height);
        if (this.showingRoutes) this.drawAllRoutes();
        if (this.showingRooms) this.drawAllRooms();
        if (this.showingPins) this.drawAllPins();
        if (this.radioMapMode) this.drawRadioMapForBSSID();


        if (evt) this.drawMouseCoordinates(evt);

        if (evt) {
            let mousePos = this.getMousePos(this.canvas, evt)
            if (this.addingPinMode) {
                // if (this.pinIsMoving && !this.doNothing) { // draw the pin where the mouse points
                //     this.ctx.drawImage(this.imgPinGreen, mousePos.x - this.imgPinGreen.width/2 +1, mousePos.y - this.imgPinGreen.height, this.imgPinGreen.width, this.imgPinGreen.height); //and then draw the pin image on top
                // } else {
                //     // pin is not moving
                //     if (this.newPin.x) { // if we have a new pin
                //         this.ctx.drawImage(this.imgPinGreen, this.newPin.x - this.imgPinGreen.width/2 +1, this.newPin.y - this.imgPinGreen.height, this.imgPinGreen.width, this.imgPinGreen.height); //and then draw the pin image on top
                //     }
                // }

            } else if (this.addingRoomMode) {
                let newRect = this.pointsToRect(mousePos.x, mousePos.y, this.startPoint.x, this.startPoint.y)
                this.drawMovingRect(this.canvas, newRect)

            } else if (this.radioMapMode) {
                if (!this.selectedBSSID) return;
                this.drawRadioMapForBSSID()

            } else if (this.fingerprintingMode) {

                if (this.doNothing) return;

                let mousePos = this.getMousePos(this.canvas, evt);
                mousePos.y = this.canvas.height - mousePos.y; // changing Origin to Bottom left

                let prevPoint = {
                    x:0,
                    y:0,
                };
                if (this.routePoints.length > 0) {
                    prevPoint = {...this.routePoints[this.routePoints.length -1]};
                    prevPoint.y = this.canvas.height - prevPoint.y; // changing Origin to Bottom left
                }

                // change Origin of coordinates to Center of Canvas
                mousePos.x = mousePos.x - Math.floor(this.canvas.width/2);
                mousePos.y = mousePos.y - Math.floor(this.canvas.height/2);
                // console.log("mouse: ", mousePos)
                prevPoint.x = prevPoint.x - Math.floor(this.canvas.width/2);
                prevPoint.y = prevPoint.y - Math.floor(this.canvas.height/2);
                // console.log("origin: ", prevPoint);

                // getting a vector with origin the last Point of the Route
                let vector = {
                    x: mousePos.x - prevPoint.x,
                    y: mousePos.y - prevPoint.y
                }
                // console.log("vector: ", vector)

                let angle = this.getAngle(vector);
                // console.log("angle: ", angle)

                // renew the prevPoint with the old Coordinates
                prevPoint = {...this.routePoints[this.routePoints.length -1]};

                if (angle > 45 && angle <= 135) {
                    // north
                    this.nextRoutePoint.x = prevPoint.x
                    this.nextRoutePoint.y = prevPoint.y - this.pointOffset;
                    if (this.routePoints[this.routePoints.length -1]) this.routePoints[this.routePoints.length -1].direction = "north"; // saving the direction in which we moved
                } else if (angle > 135 && angle <= 215) {
                    // west
                    this.nextRoutePoint.x = prevPoint.x - this.pointOffset;
                    this.nextRoutePoint.y = prevPoint.y;
                    if (this.routePoints[this.routePoints.length -1]) this.routePoints[this.routePoints.length -1].direction = "west";
                } else if (angle > 215 && angle <= 305) {
                    // south
                    this.nextRoutePoint.x = prevPoint.x
                    this.nextRoutePoint.y = prevPoint.y + this.pointOffset;
                    if (this.routePoints[this.routePoints.length -1]) this.routePoints[this.routePoints.length -1].direction = "south";
                } else {
                    // east
                    this.nextRoutePoint.x = prevPoint.x + this.pointOffset;
                    this.nextRoutePoint.y = prevPoint.y;
                    if (this.routePoints[this.routePoints.length -1]) this.routePoints[this.routePoints.length -1].direction = "east";
                }

                this.ctx.beginPath();
                this.ctx.moveTo(prevPoint.x, prevPoint.y);
                this.ctx.lineTo(this.nextRoutePoint.x, this.nextRoutePoint.y)
                this.ctx.stroke();
            } else if (this.testingMode) {
                // nothing to be done
            }
        }
    }

    getAngle(vector) {
        let angle = 0;
        if (vector.x > 0) {
            angle = Math.atan(vector.y/vector.x);
        } else if (vector.x < 0 && vector.y >= 0) {
            angle = Math.atan(vector.y/vector.x) + Math.PI;
        } else if (vector.x < 0 && vector.y < 0) {
            angle = Math.atan(vector.y/vector.x) - Math.PI;
        } else if (vector.x == 0 && vector.y > 0) {
            angle = Math.PI/2;
        } else if (vector.x == 0 && vector.y < 0) {
            angle = - Math.PI/2;
        } else if (vector.x == 0 && vector.y == 0) {
            angle = NaN;
        }
        if (angle < 0) {
            angle += 2*Math.PI; // adding this will make it from [-pi, pi] to [0, 2pi]
        }
        angle = angle * 180 / Math.PI; // convert to degrees
        return angle;
    }

    drawMouseCoordinates(evt) {
        if (!this.showMousePos) return;
        let mousePos = this.getMousePos(this.canvas, evt);
        let message = 'pos: ' + Math.floor(mousePos.x) + ',' + Math.floor(mousePos.y);
        this.ctx.clearRect(515, 565, this.canvas.width, this.canvas.height);
        this.ctx.font = '11pt Calibri';
        this.ctx.fillStyle = 'black';
        this.ctx.fillText(message, 520, 577);
    }

    drawMovingRect(canvas, newRect) {
        this.ctx.beginPath();
        this.ctx.rect(newRect.x, newRect.y, newRect.width, newRect.height);
        this.ctx.stroke();
    }

    highlightPin(pin) {
        if (this.highlightedPin != null) {
            this.unHighlightPin(this.highlightedPin);
        }

        if (pin.x) { // if we have a new pin to highlight
            this.ctx.drawImage(this.imgPinYellow, pin.x - this.imgPinYellow.width/2 +1, pin.y - this.imgPinYellow.height, this.imgPinYellow.width, this.imgPinYellow.height); //and then draw the pin image on top
        }
        this.highlightedPin = pin;
    }

    unHighlightPin(pin) {
        if (pin.x) { // if we have a new pin
            this.ctx.drawImage(this.imgPin, pin.x - this.imgPin.width/2 +1, pin.y - this.imgPin.height, this.imgPin.width, this.imgPin.height); //and then draw the pin image on top
        }
    }

    // -----------------------------------------------  Other ---------------------------------------------- //
    getMousePos(canvas, evt) {
        let rect = canvas.getBoundingClientRect();
        return {
            x: Math.floor(evt.clientX - rect.left),
            y: Math.floor(evt.clientY - rect.top)
        };
    }

    addRoom() {
        if (this.newRoom.height == 0 && this.newRoom.width == 0) {
            console.log("Invalid new Room");
            return;
        } else if (!this.newRoom.name) {
            console.log("Room has no name")
            return;
        } else {
            let roomToAdd = this.newRoom
            roomToAdd.x = roomToAdd.x / this.canvas.width;
            roomToAdd.y = roomToAdd.y / this.canvas.height;
            roomToAdd.width = roomToAdd.width / this.canvas.width;
            roomToAdd.height = roomToAdd.height / this.canvas.height;

            this.rooms.push(roomToAdd)
            this.newRoom = {
                name: '',
                x: 0,
                y: 0,
                width: 0,
                height: 0
            }
        }
        const event = new Event('closeNewRoomModal');
        this.evt.target.dispatchEvent(event);
        this.redrawAll(this.evt)
    }

    addPin() {
        if (this.newPin.x == 0 && this.newPin.y == 0) return -1;
        let pinToSend = this.newPin;
        pinToSend.x = pinToSend.x / this.canvas.width;
        pinToSend.y = pinToSend.y / this.canvas.height;
        this.pins.push(pinToSend)
        this.newPin = {
            x: 0,
            y: 0
        }
        this.pinIsMoving = true;
        return 1;
    }

    deletePin(index) {
        // this.unHighlightPin(index);
        this.pins.splice(index, 1);
        this.redrawAll(this.evt);
    }

    deleteRoute(index) {
        // this.unHighlightPin(index);
        this.routes.splice(index, 1);
        this.redrawAll(this.evt);
    }

    pointsToRect(x1, y1, x2, y2) {
        let x, y, w, h;
        if (x1 <= x2) {
            x = x1;
            w = x2 - x1;
        } else if (x2 < x1) {
            x = x2;
            w = x1 - x2;
        }

        if (y1 <= y2) {
            y = y1;
            h = y2 - y1;
        } else if (y2 < y1) {
            y = y2;
            h = y1 - y2;
        }
        return { x:Math.floor(x), y:Math.floor(y), width:Math.floor(w), height:Math.floor(h) }
    }

    dbmToQuality(dBm) {
        // where dBm: [-100 to -50]
        let quality = 0;
        if (dBm <= -100){
            quality = 0;
        } else if (dBm >= -50) {
            quality = 100;
        } else {
            quality = 2 * (dBm + 100);
        }
        return quality;
    }
}


