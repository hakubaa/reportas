window.rtab = (function(selector) {
    function RecordTable(table) {
        this.table = table;
    }
    RecordTable.prototype.test = function() {
        return this;
    }
    
    function init(selector) {
        var table = $(selector);
        if (table.length === 0) {
            throw "Element does not exist.";
        }
        return new RecordTable(table);
    }

    return init;
}());