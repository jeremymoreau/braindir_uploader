$(document).ready(function () {

    // display loading screen for 200 ms
    $('#loading_page').fadeOut(200);

    // fullPage.js configuration
    $('#fullpage').fullpage({
        verticalCentered: true,
        resize: false,
        keyboardScrolling: true
    });
    $.fn.fullpage.setAllowScrolling(false);



    ////////////////// upload_main section //////////////////
    // open file dialog to choose dir to upload
    $('#choose_dir_to_upload_btn').click(function () {
        Sijax.request('choose_dir_to_upload');
    });

    // date picker for acquisition date field
    $('#acquisition_date_field').datepicker({
        format: "yyyymmdd",
        orientation: "bottom left",
        autoclose: true
    });

    // start upload
    $('#upload_form').bind('submit', function () {
        // Get progress log file name
        window.up_prog_filename = ''.concat(
            $('#pscid_field').val(),
            '_',
            $('#dccid_field').val(),
            '_',
            $('#visit_label_field').val(),
            '_',
            $('#acquisition_date_field').val(),
            '.up_prog.json'
        );

        Sijax.request('start_upload', [
            $('#dir_to_upload_path_field').val(),
            window.up_prog_filename
        ]);

        // modify upload button
        $("#upload_button").prop("disabled", true);
        $("#upload_spinner").removeClass("fa-cloud-upload").addClass("fa-spinner fa-spin");
        $("#upload_txt").html(" Uploading…");

        //Prevent the form from being submitted
        return false;
    });

    // update progress bars in function of python backend progress
    var start_pgb_update = function updatePGB() {
        if ($('#upload_spinner').hasClass('fa-spinner')) {
            Sijax.request('update_pgb', [window.up_prog_filename]);
        }

        if ($('#pgb1-label').html() === '100%' ) {
            Sijax.request('upload_complete', [window.up_prog_filename]);
            $.fn.fullpage.moveSectionUp();
            return true;
        } else {
            setTimeout(updatePGB, 3000);
        }
    };
    start_pgb_update();

    // Validator for pscid, dccid, visit label, and acqusition date fields
    $('#upload_form').bootstrapValidator({
        container: 'tooltip',
        feedbackIcons: {
            valid: 'glyphicon glyphicon-ok',
            invalid: 'glyphicon glyphicon-remove',
            validating: 'glyphicon glyphicon-refresh'
        },
        fields: {
            pscid: {
                validators: {
                    regexp: {
                        regexp: /^[A-Z]{3}\d{4}$/,
                        message: 'The PSCID should be composed of 3 uppercase letters followed by 4 digits'
                    }
                }
            },
            dccid: {
                validators: {
                    regexp: {
                        regexp: /^\d{6}$/,
                        message: 'The DCCID should be composed of 6 digits'
                    }
                }
            },
            visit_label: {
                validators: {
                    regexp: {
                        regexp: /^V\d{2}$/,
                        message: 'The visit label should be composed of the uppercase letter "V" followed by 2 digits'
                    }
                }
            },
            acquisition_date: {
                validators: {
                    regexp: {
                        regexp: /^(19|20|21)\d{2}(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])$/,
                        message: 'The acquisition date should be formatted as yyyymmdd'
                    }
                }
            }
        }
    });

    // validate acquisition date on datepicker hide
    $('#acquisition_date_field').datepicker()
        .on('hide', function(e){
            $('#upload_form').bootstrapValidator('revalidateField', 'acquisition_date');
    });
    ////////////////// End upload_main section //////////////////

    ////////////////// Settings Dialog //////////////////
    // Check if public/private keys are loaded on app startup
    // Check if a settings.json file exists and loads settings
    // Adjust settings dialog accordingly
    Sijax.request('check_settings');


    // Display alert dialog showing the hostkey's fingerprint
    $('#load_hostkey_btn').click(function () {
        Sijax.request('get_hostkey_fingerprint', [$('#hostname_field').val()]);
    });

    // Load the hostkey
    $('#save_hostkey_btn').click(function () {
        Sijax.request('load_hostkey', [$('#hostname_field').val()]);
    });

    // Close hostkey alert
    $('#close_hostkey_alert_btn').click(function () {
        $('#hostkey_alert').hide();
        $('#load_hostkey_btn').show();
        $('#hostkey_alert > h4').html('Please verify the authenticity of host&nbsp;');
        $('#hostkey_alert > span:eq(0)').html('The authenticity of host&nbsp;');
        $('#hostkey_alert > span:eq(1)').html('RSA key fingerprint is&nbsp;');
    });

    // open file dialog to choose save path for generated public key
    $('#public_key_save_path_btn').click(function () {
        Sijax.request('choose_public_key_save_path');
    });

    // Generate public/private key pair
    $('#generate_keys_btn').click(function () {
        Sijax.request('generate_keys', [$('#public_key_save_path').val()]);

        // modify #generate_keys_btn if public_key_save_path field is not empty
        if ($('#public_key_save_path').val().length != 0) {
            $("#generate_keys_btn").prop("disabled", true).html(
                "<span class='fa fa-spinner fa-spin'></span> Generating Keys..."
            );
        }
    });

    // Save hostname, username, and upload save path to settings file
    $("#save_settings").click(function () {
        Sijax.request('save_settings', [$('#hostname_field').val(), $('#username_field').val(),
            $('#host_save_path_field').val()]);
    });

    ////////////////// End Settings Dialog //////////////////

    ////////////////// Resume Upload Modal //////////////////
    // populate resume upload modal with table of interrupted uploads
    $("#resume_btn").click(function() {
        Sijax.request('display_resume_modal');
    });

    // clear resume upload modal on close
    $("#resume_up_modal").on('hidden.bs.modal', function () {
        $("[id^='interrupted_up_']").remove();
        $('#resume_up_table').addClass('hidden');
        $('#nothing_to_resume').removeClass('hidden');
    });

    var $body = $("body");
    // delete an interrupted upload log file when corresponding Delete button is clicked
    $body.delegate('.resume_btn_delete', 'click', function() {
        var pscid = $(this).parent().siblings('.pscid').html();
        var dccid = $(this).parent().siblings('.dccid').html();
        var visit_label = $(this).parent().siblings('.visit_label').html();
        var acquisition_date = $(this).parent().siblings('.acquisition_date').html();

        Sijax.request('delete_interrupted_up_log', [pscid, dccid, visit_label, acquisition_date]);
        $(this).parent().parent().remove();
    });

    // resume an interrupted upload when corresponding Resume button is clicked
    $body.delegate('.resume_btn_resume', 'click', function() {
        var pscid = $(this).parent().siblings('.pscid').html();
        var dccid = $(this).parent().siblings('.dccid').html();
        var visit_label = $(this).parent().siblings('.visit_label').html();
        var acquisition_date = $(this).parent().siblings('.acquisition_date').html();

        Sijax.request('resume_upload', [pscid, dccid, visit_label, acquisition_date]);
        $(this).parent().parent().remove();

        // Set progress log file name (for start_pgb_update() to work)
        window.up_prog_filename = ''.concat(
            pscid, '_',
            dccid, '_',
            visit_label, '_',
            acquisition_date, '.up_prog.json'
        );

        // modify upload button
        $("#upload_button").prop("disabled", true);
        $("#upload_spinner").removeClass("fa-cloud-upload").addClass("fa-spinner fa-spin");
        $("#upload_txt").html(" Uploading…");

        // close modal dialog and move up to upload_main page
        $('#resume_up_modal').modal('hide');
        $.fn.fullpage.moveSectionUp();
    });
    ////////////////// End Resume Upload Modal //////////////////

    ////////////////// upload_complete section //////////////////
    // select text on focus
    $("#upload_location_field").focus(
        function () {
            $(this).select();
        }
    )
        .mouseup(
        function (e) {
            e.preventDefault();
        }
    );

    // return to main_menu button control
    $(".return_to_main_menu_btn").click(function () {
        // reset all fields on upload_main page
        $('#dir_to_upload_path_field').val('');
        $('#pscid_field').val('');
        $('#dccid_field').val('');
        $('#visit_label_field').val('');
        $('#acquisition_date_field').val('');

        // reset Upload button to default state
        $("#upload_button").prop("disabled", false);
        $("#upload_spinner").removeClass("fa-spinner fa-spin").addClass("fa-cloud-upload");
        $("#upload_txt").html(" Upload");

        // reset progress bar to 0 and restart progress bar update function
        $('#pgb1').width('0');
        $('#pgb1-label').html('');
        start_pgb_update();

        // reset form validation
        $('#upload_form').data('bootstrapValidator').resetForm();

        // move back to main_menu page
        $.fn.fullpage.moveTo(3);
    });

    ////////////////// upload_complete section //////////////////

     $("#main_menu_upload_btn").click(function () {
        $.fn.fullpage.moveSectionUp();
    });

    // // modify upload icon when clicked
    // $("#upload_button").click(function() {
    // 	//$("#upload_button").removeClass("btn-default").addClass("btn-success").prop("disabled", true);
    // 	$("#upload_spinner").removeClass("fa-cloud-upload").addClass("fa-spinner fa-spin");
    // 	$("#upload_txt").html(" Uploading…");
    // });
});