
// a module to create a Floor Layout object

export class FloorPlan {
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
        } else if (mode == 'rooms') {
            this.addingPinMode = false;
            this.addingRoomMode = true;
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
        }
    }

    // ---------------------------------------------  Drawing -------------------------------------------------- //
    drawAllPins() {
        this.pins.forEach(pin => {
            pin.x = pin.x * this.canvas.width <= this.canvas.width? Math.floor(pin.x * this.canvas.width) : pin.x;
            pin.y = pin.y * this.canvas.height <= this.canvas.height? Math.floor(pin.y * this.canvas.height) : pin.y;

            this.ctx.drawImage(this.imgPin, pin.x - this.imgPin.width/2 +1, pin.y - this.imgPin.height, this.imgPin.width, this.imgPin.height);
        })
    }

    drawAllRooms() {
        this.rooms.forEach((room,i) => { // room(x,y,width,height)
            room.x = room.x * this.canvas.width <= this.canvas.width? Math.floor(room.x * this.canvas.width) : room.x;
            room.y = room.y * this.canvas.height <= this.canvas.height? Math.floor(room.y * this.canvas.height) : room.y;
            room.width = room.width * this.canvas.width <= this.canvas.width? Math.floor(room.width * this.canvas.width) : room.width;
            room.height = room.height * this.canvas.height <= this.canvas.height? Math.floor(room.height * this.canvas.height) : room.height;

            // draw rect
            this.ctx.beginPath();
            this.ctx.rect(room.x, room.y, room.width, room.height);
            this.ctx.stroke();
            // draw index of rect
            this.ctx.font = '11pt Calibri';
            this.ctx.fillStyle = 'black';
            let text = (i+1) + '. ' + room.name;
            this.ctx.fillText(text, room.x+5, room.y+15);
        })
    }

    redrawAll(evt) {
        // redraw image
        this.ctx.drawImage(this.img, 0, 0, this.canvas.width, this.canvas.height);

        if (evt) {
            let mousePos = this.getMousePos(this.canvas, evt)
            if (this.addingPinMode) {
                if (this.pinIsMoving && !this.doNothing) { // draw the pin where the mouse points
                    this.ctx.drawImage(this.imgPinGreen, mousePos.x - this.imgPinGreen.width/2 +1, mousePos.y - this.imgPinGreen.height, this.imgPinGreen.width, this.imgPinGreen.height); //and then draw the pin image on top
                } else {
                    // pin is not moving
                    if (this.newPin.x) { // if we have a new pin
                        this.ctx.drawImage(this.imgPinGreen, this.newPin.x - this.imgPinGreen.width/2 +1, this.newPin.y - this.imgPinGreen.height, this.imgPinGreen.width, this.imgPinGreen.height); //and then draw the pin image on top
                    }
                }

            } else if (this.addingRoomMode) {
                let newRect = this.pointsToRect(mousePos.x, mousePos.y, this.startPoint.x, this.startPoint.y)
                this.drawMovingRect(this.canvas, newRect)
            }
        }

        if (this.showingRooms) this.drawAllRooms();
        if (this.showingPins) this.drawAllPins();
        if (evt) this.drawMouseCoordinates(evt);
    }

    drawMouseCoordinates(evt) {
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

    highlightPin(index) {
        // console.log(this.pins[index])
        let pin = this.pins[index];
        if (!pin) return;
        if (pin.x) { // if we have a new pin
            this.ctx.drawImage(this.imgPinYellow, pin.x - this.imgPinYellow.width/2 +1, pin.y - this.imgPinYellow.height, this.imgPinYellow.width, this.imgPinYellow.height); //and then draw the pin image on top
        }
    }

    unHighlightPin(index) {
        // console.log(this.pins[index])
        let pin = this.pins[index];
        if (!pin) return;
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

}


