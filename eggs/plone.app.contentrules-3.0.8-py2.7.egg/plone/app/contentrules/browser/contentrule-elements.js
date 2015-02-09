var SKIP_OVERLAY_ACTIONS = [
  'plone.actions.Delete'
];

(function ($) {
$(function () {
  function initforms(){
    $('#configure-conditions .rule-element input, #configure-actions .rule-element input').unbind('click').click(function(){
      var name = $(this).attr('name');
      if(name=='form.button.EditCondition' || name=='form.button.EditAction'){
        return true;
      }
      $('#kss-spinner').show();
      var form = $(this).parents('form').first();
      var fieldset = form.parents('fieldset').first();
      var data = form.serialize() + "&" + name + "=1";
      var url = form.attr('action');
      $.post(url, data, function(html){
        var newfieldset = $(html).find('#' + fieldset.attr('id'));
        fieldset.replaceWith(newfieldset);
        initforms();
        $('#kss-spinner').hide();
      });
      return false;
    });

    $('input[name="form.button.AddCondition"],input[name="form.button.AddAction"]').unbind('click').click(function(e){
      var form = $(this).parent().parent();
      var data = form.serialize();
      for(var i=0; i<SKIP_OVERLAY_ACTIONS.length; i++){
        if(data.indexOf(SKIP_OVERLAY_ACTIONS[i]) !== -1){
          return;
        }
      }
      e.preventDefault();
      var url = form.attr('action') + '?' + data;
      var conditionAnchor = $('<a href="' + url + '" />').css('display', 'none');
      conditionAnchor.prepOverlay({
        subtype: 'ajax',
        filter: '#content > *',
        closeselector: '[name="form.actions.cancel"]',
        formselector: '#content-core form[id="zc.page.browser_form"]',
        noform: function(el) {return $.plonepopups.noformerrorshow(el, 'redirect');},
        redirect: function(el, responseText){
          var anchor = form.parents('fieldset').children('a').first().attr('name');
          var timestamp = Math.floor(+new Date() / 1000);
          return window.location.href.split('#')[0] + '?' + timestamp + '#' + anchor;
        }
      });
      conditionAnchor.trigger('click');
    });

    /* simple overlay to trigger on forms here */
    $('.popup').prepOverlay({
      subtype: 'ajax',
      filter: '#content > *',
      closeselector: '[name="form.actions.cancel"]'
    });

  }
  initforms();

  /* To enable ajax overlay loading with the current widget
     used for the add button, we'll create a hidden anchor
     tag that'll we'll manually trigger clicks for.
     We'll add one for conditions and one for actions. */
});
}(jQuery));
