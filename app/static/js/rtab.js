window.rtab = (function(selector) {
    /*--------------------------------------------------------------------------
      Utils
    --------------------------------------------------------------------------*/
    
    //TODO: MOVE TO CONFIGS
    var UNDEFINED_RTYPE = "undefined";
    var UNDEFINED_TIMERANGE = " --- ";
    var UNDEFINED_TIMESTAMP = " --- ";
    var EMPTY_RTYPE = " --- SELECT RECORD TYPE --- ";


    function setValueOfElement(element, value) {
        switch (element.prop("tagName").toLowerCase()) {
            case "input":
                element.val(value);
                break;
            case "select":
                element.val(value).trigger("change");
                break;
            default:
                element.text(value);
                break;
        }
    }
    
    function readValueOfElement(element) {
        switch (element.prop("tagName").toLowerCase()) {
            case "input":
            case "select":
                return element.val();
            default:
                return element.text();
        }
    }
    
    function populateRowWithData(row, data) {
        if (data === undefined) data = {"rtype": undefined, "values": []}
        
        var valueInputs = row.find(".record-value");
        for (var i = 0; i < valueInputs.length; i++) {
            var value = data.values.length > i ? data.values[i] : 0;
            setValueOfElement($(valueInputs[i]), value);
        }
        if (data.rtype !== undefined) {
            setValueOfElement(row.find(".record-rtype"), data.rtype);
            row.attr("data-record-rtype", data.rtype);
        }
        if (data.uom !== undefined) {
            setValueOfElement(row.find(".record-uom"), data.uom);
        }
    }
    
    function createNewRow(numberOfValueInputs, attributes, columns) {
        if (numberOfValueInputs === undefined) numberOfValueInputs = 0;
        if (attributes === undefined) attributes = {};
        if (columns === undefined) columns = [];

        attributes = $.extend({
                "class": "record-row",
                "data-record-type": UNDEFINED_RTYPE
            }, attributes
        );
        
        var $row = $("<tr></tr>", attributes);
        for (var i = 0; i < columns.length; i++) {
            $row.append(
                wrapWith("td", 
                    columns[i].factory_method(), 
                    columns[i].attributes
                )
            );
        }

        $row.append(createRecordTypeCell());
        $row.append(createUOMCell());
        for (var i = 0; i < numberOfValueInputs; i++) {
            $row.append(createInputValueCell());
        }
    
        return $row;
    }
    
    function createRecordTypeCell(attributes) {
        var defaultAttributes = {"class": "cell-rtype"};
        $.extend(defaultAttributes, attributes);
    
        var $cell = wrapWith("td", [
                $("<span></span>", {"class": "record-rtype", "text": ""}),
                $("<span></span>", {
                    "class": "record-rtype-select-msg", "text": EMPTY_RTYPE}
                ),
                wrapWith("a",
                    $("<span></span>", {"class": "glyphicon glyphicon-list"}),
                    {
                        "href": "javascript:void(0);", "class": "record-rtype-btn",
                        "tabindex": "-1"
                    }    
                ),
                defaultAttributes
            ]
        );
        return $cell;
    }
    
    function createUOMCell(attributes) {
        var defaultAttributes = {"class": "cell-uom"};
        $.extend(defaultAttributes, attributes);
    
        var $cell = wrapWith("td",
            $("<select></select>", {"class": "record-uom", "tabindex": "-1"}),
            defaultAttributes
        );
        return $cell;    
    }
    
    function createInputValueCell(attributes) {
        var defaultAttributes = {"class": "cell-value"};
        $.extend(defaultAttributes, attributes);
    
        var $cell = wrapWith("td", 
            createRecordInputValue(), defaultAttributes
        );
        return $cell;     
    }
    
    function createRecordInputValue(value) {
        return $("<input></input>", {
                "type": "text",
                "class": "form-control input-sm record-value",
                "val": (value ? value !== undefined : 0)
            });
    }
    
    function createHeaderElement(data) {
        if (data === undefined) data = {};
        var timerange = data.timerange;
        if (timerange === undefined) timerange = UNDEFINED_TIMERANGE;
        var timestamp = data.timestamp;
        if (timestamp == undefined) timestamp = UNDEFINED_TIMESTAMP;
        
        var $th = $("<th></th>", {"class": "column-value"});
        $("<span></span>", {
            "class": "timerange","text": timerange
        }).appendTo($th);
        $("<span> months ended on </span>").appendTo($th);
        $("<span></span>", {
            "class": "timestamp", "text": timestamp
        }).appendTo($th);
        $("<span> </span>").appendTo($th);
        $("<a></a>", {
            "href": "javascript:void(0);",
            "class": "time-editor-btn",
            "html": "<span class='glyphicon glyphicon-edit'></span>"
        }).appendTo($th);
        $("<a></a>", {
            "href": "javascript:void(0);",
            "class": "column-remove-btn",
            "html": "<span class='glyphicon glyphicon-remove'></span>"
        }).appendTo($th);            
        return $th;
    }

    function getIDforRType(name, rtypes) {
        var matchedRTypes = $.grep(rtypes, function(obj) { 
            return (obj.name == name); 
        });
    
        var recordId = undefined;
        if (matchedRTypes.length > 0) {
            recordId = String(matchedRTypes[0].id);
        }
        return recordId;
    }

    function toggleTable(table) {
        var numberOfRows = table.find("tbody tr:visible").not(".empty-row").length;
        if (numberOfRows === 0) { // show empty row
            table.find(".empty-row").show();
            // table.find("thead").hide();
        } else {
            var $firstRow = table.find("tbody tr:visible:first");
            if ($firstRow.hasClass("empty-row") && numberOfRows > 0) {
                $firstRow.hide();
                // table.find("thead").show();
            } 
        }
    }

    function bindEvents(selector, rtypes) {
        $(document).on("click", selector + " .record-remove-btn", function() {
            var $table = $(this).closest("table");
            $(this).closest("tr").remove();
            toggleTable($table);
        });

        $(document).on("click", selector + " .record-rtype-btn", function() {
            var $self = $(this);
            var recordId = getIDforRType(
                $self.closest("td").find(".record-rtype").text(), rtypes
            );
            var dialog = createRTypeSelectionDialog({
                data: rtypes, text: "name", 
                initval: recordId,
                callback: function(rtype) {
                    var $row = $self.closest("tr");
                    $self.closest("td").find(".record-rtype").text(rtype.text);
                    $row.attr("data-record-rtype", rtype.text);
                    $row.attr("data-record-id'", rtype.id);
                    $row.find("span.record-rtype-select-msg").remove();

                    if (rtype.text in fschema_formulas) {
                        $row.find("td.cell-calculable input").prop("disabled", false);
                    }

                }
            });
            dialog.open();
        });

        $(document).on("click", selector + " .time-editor-btn", function() {
            var $timerange = $(this).parent().find(".timerange");
            var $timestamp = $(this).parent().find(".timestamp");
            var dialog = createTimeSelectionDialog({
                "timerange": $timerange,
                "timestamp": $timestamp
            });
            dialog.open();
        });

        $(document).on("click", selector + " .column-remove-btn", function() {
            if (confirm("Are your sure you want to remove whole columne?") === true) {
                var $column = $(this).closest("th");
                var $table = $(this).closest("table");
                rtab.bind($table).removeColumn(
                    $table.find("thead th.column-value").index($column)
                );
            }
        });

        $(document).on("change", selector + " td.cell-value > input", function() {
            var $row = $(this).closest("tr");
            var rtype_trigger = $row.attr("data-record-rtype");
            var cindex = $row.find("td.cell-value").index($(this).closest("td"));
            rtab.bind($(this).closest("table")).updateRecords(rtype_trigger, cindex);
        });

        $(document).on("change", selector + " td.cell-uom > select", function() {
            var $row = $(this).closest("tr");
            var rtype_trigger = $row.attr("data-record-rtype");
            var rt = rtab.bind($(this).closest("table"));
            rt.updateRecords(rtype_trigger);
        });

        $(document).on("change", selector + " td.cell-calculable > input", function() {
            if ($(this).is(":checked")) {
                $(this).closest("tr").addClass("row-calculable");
                $(this).closest("tr").find("td.cell-value input").prop("disabled", true);

                var rtype_trigger = $(this).closest("tr").attr("data-record-rtype");
                var rt = rtab.bind($(this).closest("table"));
                rt.updateRecords(rtype_trigger);
            } else {
                $(this).closest("tr").removeClass("row-calculable");
                $(this).closest("tr").find("td.cell-value input").prop("disabled", false);
            }
        });

    }

    function activateFocusOnInputs(selector) {
        $(document).on("focusin", selector + " td input[type=text]", function() {
            $(this).closest("tr").addClass("info"); 
        });
        
        $(document).on("focusout", selector + " td input[type=text]", function() {
            $(this).closest("tr").removeClass("info"); 
        });
    }

    function getTable(selector) {
        var $table;
        if (typeof selector === "string") {
            $table = $(selector); 
        } else {
            $table = selector;
        }
        if ($table.length === 0) throw "Element does not exist."; 
        if ($table.prop("tagName").toLowerCase() !== "table") {
            throw "Element is not a table.";
        }
        return $table;
    }

    function findDuplicateRecords(table) {
        var records = table.find("tbody tr").map(function(rowIndex) {
            var recordType = $(this).find("td").find(".record-rtype").text();
            return recordType;
        }).get();

        var recordsCounter = {};
        for (var i = 0; i < records.length; i++) {
            if (records[i] === "") continue;
            if (!(records[i] in recordsCounter)) {
                recordsCounter[records[i]] = 0;
            }
            recordsCounter[records[i]] += 1;
        }

        var duplicatedRecords = [];
        for (var property in recordsCounter) {
            if (recordsCounter.hasOwnProperty(property)) {
                if (recordsCounter[property] > 1) {
                    duplicatedRecords.push(property);
                }
            }
        }
        return duplicatedRecords;
    }

    function isFormulaCalculable(formula, records) {
        var components = formula.components;
        for (var i = 0; i < components.length; i++) {
            if (records.indexOf(components[i].rtype) < 0) {
                return false;
            }
        }
        return true;
    }

    function calculateFormula(formula, data) {
        var value = formula.components.map(function(item) {
            return parseInt(item.sign) * data[item.rtype];
        }).reduce(function(x, y) { return x + y; }, 0);
        return value;
    }

    function groupBy(array, f){
        var groups = {};
        array.forEach(function(o) {
            var group = JSON.stringify(f(o));
            groups[group] = groups[group] || [];
            groups[group].push(o);  
        });
        return Object.keys(groups).map(function(group) {
            return groups[group]; 
        });
    }

    function isArrayHomo(array) {
        var first = array[0];
        return array.every(function(element) {
            return element === first;
        });
    }

    /*--------------------------------------------------------------------------
      RecordTable
    --------------------------------------------------------------------------*/
    
    function RecordTable(table, configs) {
        this.$table = table;
        this.configs = jQuery.extend({}, configs); /* local configs */
    }
    
    RecordTable.prototype.config = function(key, value) {
        if (value === undefined) {
            return this.configs[key];
        }
        this.configs[key] = value;
    }
    
    RecordTable.prototype.getRTypes = function() {
        return this._get("rtypes");
    }
    
    RecordTable.prototype.getUOM = function() {
        return this._get("uom");
    }

    RecordTable.prototype.getFormulas = function() {
        return this._get("formulas");
    }

    RecordTable.prototype._get = function(name, cache_name) {
        if (cache_name === undefined) cache_name = name;
        if (this[cache_name] !== undefined) return this[cache_name];
        if (this.config(name) === undefined) return undefined;

        if (typeof this.config(name) === "function") {
            this[cache_name] = this.config(name)();
        } else {
            this[cache_name] = this.config(name);
        }
        return this[cache_name];
    }
    
    RecordTable.prototype.addRow = function(data, attributes) {
        var $row = createNewRow(this.ncols, attributes, this.config("columns"));
        $row.find(".record-uom").bindUnitsOfMeasure(this.getUOM());
        if (data !== undefined) populateRowWithData($row, data);
        this.$table.find("tbody").append($row); 
    }
    
    RecordTable.prototype.addColumn = function(data) {
        var column = [];
        column.push(this.$table.find("thead tr").append(
            createHeaderElement(data)
        ));
        var rows = this.$table.find("tbody tr").not(".empty-row");
        for(var i = 0; i < rows.length; i++) {
            column.push($(rows[i]).append(
                wrapWith("td", createRecordInputValue(), {"class": "cell-value"})
            ));    
        }
        return column;
    }

    RecordTable.prototype.getData = function(companyId) {
        if (companyId === undefined) companyId = null;
        
        var self = this;
        var headers = this.getDataHeaders();
        var records = this.$table.find("tbody tr:not(.empty-row)").map(function(rowIndex) {
            var rtype = $(this).attr("data-record-rtype");
            var uom = parseInt($(this).find("select.record-uom").val());
            if (isNaN(uom)) uom = 1;
            return $(this).find("td.cell-value").map(function(columnIndex) {
                return {
                    "company_id": companyId,
                    "value": parseFloat($(this).find("input").val()) * uom,
                    "rtype_id": getIDforRType(rtype, self.getRTypes()),
                    "timerange": parseInt(headers[columnIndex].timerange),
                    "timestamp": appendLastDayOfMonth(headers[columnIndex].timestamp)
                }       
            }).get();
        }).get();
    
        return records;
    }
    
    RecordTable.prototype.getDataHeaders = function() {
        var headers = this.$table.find("thead tr th.column-value").map(function() {
            return {
                "timerange": $(this).find(".timerange").text(),
                "timestamp": $(this).find(".timestamp").text()
            };
        }).get();
        return headers;
    }

    RecordTable.prototype.removeColumn = function(index) {
        if (index !== undefined && index < this.ncols) {
            this.$table.find("thead tr").each(function() {
                $($(this).find("th.column-value")[index]).remove();
            });
            this.$table.find("tbody tr").each(function() {
                $($(this).find("td.cell-value")[index]).remove();
            });
        }
    }

    RecordTable.prototype.getRowsRTypes = function() {
        var rtypes = this.$table.find("tbody tr").map(function() { 
            return $(this).attr("data-record-rtype"); 
        }).get();
        return rtypes;
    }
    
    RecordTable.prototype.indexOf = function(rtype) {
        var $row = this.rowOf(rtype);
        if ($row.length === 0) {
            return -1;
        }
        return this.$table.find("tbody tr").index($row);
    }
    
    RecordTable.prototype.rowOf = function(rtype) {
        return this.$table.find("tbody tr[data-record-rtype='" + rtype + "']");
    }

    RecordTable.prototype.getDataFromColumn = function(cindex) {
        if (cindex > this.ncols) {
            return {};
        }
        var rows = this.$table.find("tbody tr:not(.empty-row)");
        var data = rows.map(function() { 
            var rtype = $(this).attr("data-record-rtype");
            var uom = parseInt($(this).find("td.cell-uom select").val());
            if (isNaN(uom) || uom === undefined) uom = 1;
            var value = uom * parseFloat($($(this).find("td.cell-value input")[cindex]).val());

            var result = {};
            result[rtype] = value;
            return result;
        }).get().reduce(function(x, y) {
            return $.extend(x, y);
        }, {});

        return data;
    }

    RecordTable.prototype.setValue = function(rtype, cindex, value) {
        var $row = this.rowOf(rtype);
        $row.each(function() {
            var uom = $(this).find("td.cell-uom select").val();
            if (isNaN(uom) || uom === undefined) uom = 1;
            $($(this).find("td.cell-value input")[cindex]).val(value / uom);
        });
    };

    RecordTable.prototype.updateRecords = function(rtype_trigger, cindex, exclude) {
        if (exclude === undefined) exclude = [];
        if (cindex === undefined) {
            cindex = Array.apply(null, {length: this.ncols}).map(Function.call, Number);
        } else if (!$.isArray(cindex)) {
            cindex = [cindex];
        }
        
        var formulas = this.getFormulas();
        if (formulas === undefined) return;
        if (!(rtype_trigger in formulas)) return;

        var self = this;
        var rtype_formulas = formulas[rtype_trigger].filter(function(formula) {
            return (isFormulaCalculable(formula, self.getRowsRTypes()) &&
                self.isCalculable(formula.rtype));
        });

        for (var i in rtype_formulas) {
            for (var j in cindex) {
                var rid = rtype_formulas[i].rtype + "_" + cindex[j];
                if (exclude.indexOf(rid) >= 0) continue;

                var data = this.getDataFromColumn(cindex[j]);
                this.setValue(
                    rtype_formulas[i].rtype, cindex[j],
                    calculateFormula(rtype_formulas[i], data)
                );

                exclude.push(rid);
                this.updateRecords(rtype_formulas[i].rtype, cindex[j], exclude);
            }
        }
    }

    RecordTable.prototype.isCalculable = function(rtype) {
        var $row = this.rowOf(rtype);
        if ($row.length === 0) {
            return false;
        }

        return $row.map(function() {
            return $(this).hasClass("row-calculable");
        }).get().reduce(function(x, y) { return x && y; }, true);
    }

    /*--------------------------------------------------------------------------
      Validators
    --------------------------------------------------------------------------*/

    RecordTable.prototype.validateHeaders = function() {
        var headers = this.getDataHeaders();
        var result = true;
        var details = headers.map(function(header, index) {
            result = result && !isNaN(header.timerange) 
                        && moment(header.timestamp).isValid();
            return {
                "timerange": !isNaN(header.timerange),
                "timestamp": moment(header.timestamp).isValid(),
                "index": index
            };
        });
        return {"result": result, "details": details};
    }

    RecordTable.prototype.validateRecords = function() {
        var result = true;
        var columnNumbers = this.$table.find("thead th").length;
        var details = this.$table.find("tbody tr:not(.empty-row)").map(function(index) {
            var numberOfCells = $(this).find("td").length;
            var cells = $(this).find("td.cell-value").map(function(index) {
                result = result && !isNaN($(this).find("input").val());
                return {
                    "value": !isNaN($(this).find("input").val()),
                    "index": index
                };
            }).get();
            return {
                "rows": numberOfCells == columnNumbers,
                "cells": cells,
                "index": index,
                "rtype": $(this).find(".record-rtype").text()
            };
        }).get();
        return {"result": result, "details": details};
    }

    RecordTable.prototype.validateRTypes = function() {
        var result = true;
        var details = this.$table.find("tbody tr").map(function(index) {
            var rtype = $(this).attr("data-record-rtype");
            result = result && rtype !== UNDEFINED_RTYPE;
            return {"index": index, "rtype": rtype};
        }).get();
        return {"result": result, "details": details};
    }

    RecordTable.prototype.validateRecordsDuplication = function () {
        var records = findDuplicateRecords(this.$table);
        return {"result": records.length === 0, "details": records};
    }

    /*--------------------------------------------------------------------------
      Getters
    --------------------------------------------------------------------------*/

    Object.defineProperty(RecordTable.prototype, "ncols", {
        get: function() { 
            return this.$table.find("thead tr th.column-value").length;
        }
    });
 
    Object.defineProperty(RecordTable.prototype, "nrows", {
        get: function() { 
            return this.$table.find("tbody tr").length;
        }
    });
    
    /*--------------------------------------------------------------------------
      Controler
    --------------------------------------------------------------------------*/
    
    rtab = {
        configs: { /* global configs */
            //TODO: MOVE THIS OUTSIDE THIS FILE
            uom: [ 
                {id: 1, text: "PLN"},
                {id: 1000, text: "k'PLN"},
                {id: 1000000, text: "m'PLN"}
            ]
        }, 
        config: function(key, value) {
            if (value === undefined) {
                return this.configs[key];
            } 
            this.configs[key] = value;
        },
        bind: function(selector) {
            return new RecordTable(getTable(selector), this.configs); 
        },
        bindEvents: function(selector, rtypes) {
            activateFocusOnInputs(selector);
            bindEvents(selector, rtypes);
        }
    };

    return rtab;
}());