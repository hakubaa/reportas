/**
 * Send XMLHttpRequest for identification of records.
 * @param {string} text with information for retrival
 * @param {string} type of statment (bls, nls, cfs) 
 * @param {function} callback function 
 */
function identifyRecords(text, spec, callback) {
    if (spec === undefined) spec = "";
    $.post(
        "/reports/parser", 
        { text: text, spec: spec }
    )
        .done(function(response) {
            if (callback !== undefined) {
                callback(response);
            }
        })
        .fail(function(xhr, textStatus, error){
              console.log(xhr.statusText);
              console.log(textStatus);
              console.log(error);
              alert("Error: " + error);
        });
}