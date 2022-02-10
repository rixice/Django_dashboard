window.onload = function () {

    document.getElementById('management').style.borderRightWidth = '10px';
    document.getElementById('management').style.borderRightStyle = 'solid';
    document.getElementById('management').style.borderRightColor = 'rgba(25,25,112,1)';
    document.getElementById('management').style.backgroundColor = 'rgba(25,25,112,0.6)' ;
    document.getElementById('management').style.width = '200px';

}

function get_status(host_ip){
    $.ajax({
        url: 'management',
        type: 'POST',
        data: {
            ip: host_ip
        },
        dataType:"json",
        success: function (data) {
            document.getElementById(data.host).innerHTML = data.status;
        }
    })
}

