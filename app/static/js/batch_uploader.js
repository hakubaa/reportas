$(document).ready(function() {
    $("select.record-uom").bindUnitsOfMeasure();
    $("#company-select").applySelect2();

    $("#report-disable-btn").change(function() {
        if ($(this).is(":checked")) {
            $("#report-data").hide();
        } else {
            $("#report-data").show();
        }
    });

    $(document).on("click", ".report-time-editor-btn", function() {
        var $timerange = $(this).parent().find(".timerange");
        var $timestamp = $(this).parent().find(".timestamp");
        var dialog = createTimeSelectionDialog({
            "timerange": $timerange,
            "timestamp": $timestamp
        });
        dialog.open();
    });

    rtab.config("rtypes", rtypes);
    rtab.config("columns", [ 
        {
            "factory_method": createRecordRemoveButton,
            "attributes": {"class": "cell-btn"}
        }, 
        {
            "factory_method": createCalculableCheckbox,
            "attributes": {"class": "cell-calculable"}
        }
    ]);
    rtab.bindEvents("#identified-records", rtypes);


    $(document).on("change", "td.cell-value > input", function() {
        var rtype_trigger = $(this).closest("tr").attr("data-record-rtype");
        var columnIndex = $(this).closest("td").index();
        var table = $(this).closest("table");
        updateRecords(rtype_trigger, table, columnIndex);
    });


    $(document).on("change", "td.cell-uom > select", function() {
        var rtype_trigger = $(this).closest("tr").attr("data-record-rtype");
        var columns = $(this).closest("tr").find("td.cell-value");
        var table = $(this).closest("table");
        for (var i = 0; i < columns.length; i++) {
            updateRecords(rtype_trigger, table, $(columns[i]).index());
        }
    });


    $(document).on("change", "td.cell-calculable > input", function() {
        if ($(this).is(":checked")) {
            $(this).closest("tr").addClass("row-calculable");
            $(this).closest("tr").find("td.cell-value input").prop("disabled", true);

            var rtype_trigger = $(this).closest("tr").attr("data-record-rtype");
            var columns = $(this).closest("tr").find("td.cell-value");
            var table = $(this).closest("table");
            for (var i = 0; i < columns.length; i++) {
                updateRecords(rtype_trigger, table, $(columns[i]).index());
            }
        } else {
            $(this).closest("tr").removeClass("row-calculable");
            $(this).closest("tr").find("td.cell-value input").prop("disabled", false);
        }
    });

});


function addEmptyRow(selector) {
    rtab.bind(selector).addRow();
}


function addEmptyColumn(selector) {
    rtab.bind(selector).addColumn();
}


function exportData() {
    var data = createDataForExport(rtab.bind("#identified-records"));
    if (data.records === undefined || data.records.length === 0) {
        BootstrapDialog.alert({
            title: "Validation Data - Errors",
            message: "Nothing to export. There are not any records in the table.",
            type: BootstrapDialog.TYPE_DANGER
        });
    } else {
        submitExportForm(JSON.stringify(data), validateData, function(result) {
            if (result) {
                $("#export-data-form").submit();
            }
        });
    }
    return false;
}


function validateData() {
    var val_table = validateDataInTable(rtab.bind("#identified-records"));
    var alerts = val_table.alerts;

    var val_company = validateCompany();
    alerts.push(createAlertForCompanyValidation(val_company.details));

    if (!$("#report-disable-btn").is(":checked")) {
        var val_report = validateReport();
        alerts.push(createAlertForReportValidation(val_report.details));
    }

    return {
        "result": val_table.result && val_company.result, 
        "alerts": alerts.filter(function(item) { 
            return item !== null && item !== undefined 
        })
    };
}


function updateRecords(rtype, table, columnIndex) {
    if (rtype in fschema_formulas) {
        var formulas = fschema_formulas[rtype];
        var recordsInTable = getRTypesFromTable(table);

        for (var i = 0; i < formulas.length; i++) {
            // if (rtype === formulas[i].rtype) {
            //     continue;
            // }
            if (recordsInTable.indexOf(formulas[i].rtype) < 0 || !isFormulaCalculable(formulas[i], table)) {
                continue;
            }
            var value = calculateFormula(formulas[i], table, columnIndex);
            setValueOfRecord(formulas[i].rtype, value, table, columnIndex);
        }
    }
}

function setValueOfRecord(rtype, value, table, columnIndex) {
    var row = table.find("tbody tr[data-record-rtype='" + rtype + "']");
    for (var i = 0; i < row.length; i++) {
        if (!$(row[i]).find("td.cell-calculable input").is(":checked")) {
            continue;
        }
        var uom = parseInt($(row[i]).find("td.cell-uom select").val());
        $($(row[i]).children("td")[columnIndex]).find("input").val(value / uom);
    }
}

function calculateFormula(formula, table, columnIndex) {
    var components = formula.components;
    var value = 0;
    for (var i = 0; i < components.length; i++) {
        var row = table.find("tbody tr[data-record-rtype='" + components[i].rtype + "']");
        for (var j = 0; j < row.length; j++) {
            var rtype_value = parseFloat($($(row[j]).children("td")[columnIndex]).find("input").val());
            var uom = parseInt($(row[j]).find("td.cell-uom select").val());
            value += parseInt(components[i].sign) * rtype_value * uom;
        }
    }
    return value;
}

function isFormulaCalculable(formula, table) {
    var components = formula.components;
    var recordsInTable = getRTypesFromTable(table);
    for (var i = 0; i < components.length; i++) {
        if (recordsInTable.indexOf(components[i].rtype) < 0) {
            return false;
        }
    }
    return true;
}

function getRTypesFromTable(table) {
    var rtypes = table.find("tbody tr").map(function() { 
        return $(this).attr("data-record-rtype"); 
    }).get();
    return rtypes;
}