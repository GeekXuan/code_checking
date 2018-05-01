$(document).ready(function () {
    var table = $('#table').DataTable({
        // "dom": '<"row"<"col-md-4" l><"col-md-4" f><"col-md-4 pull-right" <"ml-170"B>>>rtip',
        "DT_RowId": "row",
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "teacher"},
            {"data": "create_time"},
            {"data": "status"},
            {"data": "student_number"},
            {"data": "operation"},
        ],
        "lengthMenu": [[10, 20, 50, -1], [10, 20, 50, "All"]],
        "language": {
            'loadingRecords': '加载中...',
            'processing': '查询中...',
            'search': '查询:',
            "lengthMenu": "每页 _MENU_ 条数据",
            "info": "共 _TOTAL_ 条数据，当前为第 _PAGE_ 页, 共 _PAGES_ 页",
            "infoEmpty": "没有数据",
            "emptyTable": "没有数据",
            "paginate": {
                "next": "下页",
                "previous": "上页"
            }
        },

        "ordering": false,
        "bServerSide": true,
        "bProcessing": true,
        "serverSide": true,
        "deferLoading": $("[name=def_count]").val(),//Only effective with "bServerSide"
        "ajax": {
            "url": "#",
            "type": "GET",
        }
    });
    table.ajax.reload().draw();
    $(document).on('click', '[action]', function () {
        let action = $(this).attr("action");
        let task_id = $(this).val();
        let data = {
            "task_id": task_id,
        };
        if (action == "remove"){
            $.ajax({
                type: 'POST',
                url: '/a/remove_task/',
                data: {data: JSON.stringify(data)},
                success: function (data) {
                    if (data == 1) {
                        // alert("移除成功");
                        table.ajax.reload(null, false);
                    } else {
                        alert("移除失败");
                    }
                }
            });
        }
    });
});