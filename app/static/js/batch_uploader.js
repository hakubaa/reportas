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
    rtab.config("formulas", fschema_formulas);
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
});


function addEmptyRow(selector) {
    rtab.bind(selector).addRow();
}


function addEmptyColumn(selector) {
    rtab.bind(selector).addColumn();
}


function exportData(event) {
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