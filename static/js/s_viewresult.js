$(document).ready(function () {
    $(document).on('click', '[action]', function () {
        let action = $(this).attr("action");
        let ids = $(this).val().split('_');
        if (action == "detail"){
            let data = [{ name: "task_id", value: ids[0]}, { name: "result_id", value: ids[1]}, { name: "stu_id", value: ids[2]}];
            let temp_form = document.createElement("form");
            temp_form.action = '/s/view_detail/';
            //如需打开新窗口，form的target属性要设置为'_blank'
            temp_form.target = "_self";
            temp_form.method = "post";
            temp_form.style.display = "none";
            //添加参数
            for (let item in data) {
                let opt = document.createElement("textarea");
                opt.name = data[item].name;
                opt.value = data[item].value;
                temp_form.appendChild(opt);
            }
            document.body.appendChild(temp_form);
            //提交数据
            temp_form.submit();
        }
    });
});