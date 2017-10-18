function OutOfColorsError() {}


function SequenceColorPicker(colors, loop) {
    this.colors = colors;
    this.loop = loop === undefined ? true : loop;
    this.index = 0;
}

SequenceColorPicker.prototype.next = function() {
    return this.getColor(this.getNextColorIndex());
}

SequenceColorPicker.prototype.getColor = function(index) {
    return this.colors[index];
}

SequenceColorPicker.prototype.getNextColorIndex = function() {
    var currentIndex = this.index;
    if (currentIndex >= this.colors.length) {
        if (this.loop === true && this.colors.length > 0) {
            currentIndex = 0;
        } else {
            throw new OutOfColorsError("Color picker out of colors.");
        }
    }
    this.index = currentIndex + 1;
    return currentIndex;
}

SequenceColorPicker.prototype.random = function() {
    return this.getColor(this.getRandomIndex());
}

SequenceColorPicker.prototype.getRandomIndex = function() {
    return Math.floor(Math.random() * this.colors.length);    
}

SequenceColorPicker.prototype.reset = function() {
    this.index = 0;
}