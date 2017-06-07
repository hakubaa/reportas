/**
 * Send XMLHttpRequest for identification of records.
 * @param {Object} options 
 */
function identifyRecords(options) {
    if (options === undefined) options = {};
    if (options.spec === undefined) options.spec = "";
    if (options.text === undefined) {
        throw "Undefined text.";
    }

    $.post(
        "/reports/parser", 
        { text: options.text, spec: options.spec }
    )
        .done(function(response) {
            if (options.callback !== undefined) {
                options.callback(response);
            }
        })
        .fail(function(xhr, textStatus, error){
              console.log(xhr.statusText);
              console.log(textStatus);
              console.log(error);
              alert("Error: " + error);
        });
}