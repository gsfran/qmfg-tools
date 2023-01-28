{# $(document).ready(function() {
    $("#work_order").click(function() {
        window.open('/view-work-order.html.jinja', )
    })
}) #}

{# function onDragStart(event) {
    event.currentTarget.style.opacity = '0.2';
    event.dataTransfer.setData('text/plain', event.target.id);
}

function onDragEnd(event) {
    event.currentTarget.style.opacity = '1.0';
}

let workOrders = document.querySelectorAll('.parking_lot .work_order');
workOrders.forEach((workOrder) => {
    workOrder.addEventListener('onclick', onClick);
    workOrder.addEventListener('dragstart', onDragStart);
    workOrder.addEventListener('dragend', onDragEnd);
});

let machineRows = document.querySelectorAll('.hour');
machineRows.forEach((machineRow) => {
    machineRow.addEventListener('dragover', (e) => {
        e.preventDefault();
    });
    machineRow.addEventListener('drop', (e) => {
        var data = e.dataTransfer.getData('text/html');
        e.target.appendChild(document.getElementById(data));
    });
}) #}