function get_status(file){
    $.ajax({
        url: 'backup',
        type: 'POST',
        data: {
            file: file
        },
        dataType:"json",
        success: function (data) {
            document.getElementById(data.file).innerHTML = data.size;
            if (data.check == 'ok'){
                location.reload();
            }
        }
    })
}