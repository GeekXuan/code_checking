$(document).ready(function () {
    var table = $('#table').DataTable({
        // "dom": '<"row"<"col-md-4" l><"col-md-4" f><"col-md-4 pull-right" <"ml-170"B>>>rtip',
        "DT_RowId": "row",
        "columns": [
            {"data": "id"},
            {"data": "name"},
            {"data": "gender"},
            {"data": "class_name"},
            {"data": "status"},
            {"data": "operation"}
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
        // "createdRow": function (row, data, dataIndex) {
        //     var buttonStr = '<button action="toggle" class="btn btn-primary btn-xs">开启/关闭</button>';
        //     $(row).find('td').last().html(buttonStr);
        // },

        "ordering": false,
        "bServerSide": true,
        "bProcessing": true,
        "serverSide": true,
        "deferLoading": $("[name=def_count]").val(),//Only effective with "bServerSide"
        "ajax": {
            "url": location.href,
            "type": "GET",
        }
    });
    table.ajax.reload().draw();
    $(document).on('click', '[action]', function () {
        let action = $(this).attr("action");
        let stu_id = $(this).val();
        let task_id = location.search.slice(8);
        let data = {
            "stu_id":stu_id,
            "task_id":task_id,
        };
        if (action == "remove"){
            $.ajax({
                type: 'POST',
                url: '/t/remove_student/',
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
        }else if (action == "add"){
            $.ajax({
                type: 'POST',
                url: '/t/add_student/',
                data: {data: JSON.stringify(data)},
                success: function (data) {
                    if (data == 1) {
                        // alert("添加成功");
                        table.ajax.reload(null, false);
                    } else {
                        alert("添加失败");
                    }
                }
            });
        }
    });
});