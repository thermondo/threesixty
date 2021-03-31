const $ = window.$
class Question {
  constructor (userCanSkip) {
    this.answered = false
    this.submitNo = this.submitNo.bind(this)
    this.submitYes = this.submitYes.bind(this)
    this.submitSkip = this.submitSkip.bind(this)
    this.reset = this.reset.bind(this)
    this.swipeStatus = this.swipeStatus.bind(this)
    this.$yes = $('.yes')
    this.select = $('#id_decision')
    this.undo = $('#id_undo')
    this.undo.attr('value', 'false')
    this.select.find('option[value="1"]').removeAttr('selected')
    this.form = $('form')[0]
    this.$no = $('.no')
    this.$skip = $('.skip')
    this.$undo = $('.undo')
    this.$body = $('.question-wrapper')
    this.$body.swipe(this)
    this.userCanSkip = userCanSkip
    $(document).on('keydown', e => {
      if (!$('#search:focus').length) {
        if (!this.answered) {
          if (e.keyCode === 37) {
            this.submitUndo()
            return false
          }
          if (e.keyCode === 38) {  // up
            this.submitYes()
            return false
          }

          if (e.keyCode === 40) {  // down
            this.submitNo()
            return false
          }

          if (e.keyCode === 39 && this.userCanSkip) {  // right
            this.submitSkip()
            return false
          }
        }
      }
    })
  }

  submitNo () {
    this.answered = true
    this.select.find('option[value="false"]').attr('selected', 'selected').parent().trigger('change') // 3 = No
    this.$yes.height(0)
    this.$skip.width(0)
    this.$undo.width(0)
    this.$no.animate({height: '100%'}, {duration: 250, start: this.$no.height(), complete: () => this.form.submit()})
  }

  submitYes () {
    this.answered = true
    this.select.find('option[value="true"]').attr('selected', 'selected').parent().trigger('change') // 2 = Yes
    this.$no.height(0)
    this.$skip.width(0)
    this.$undo.width(0)
    this.$yes.animate({height: '100%'}, {duration: 250, start: this.$yes.height(), complete: () => this.form.submit()})
  }

  submitSkip () {
    this.answered = true
    this.select.find('option[value="unknown"]').attr('selected', 'selected').parent().trigger('change') // 1 = Unknown == skip
    this.$no.height(0)
    this.$yes.height(0)
    this.$undo.width(0)
    this.$skip.animate({left: '0%', width: '100%'}, {duration: 250, start: this.$skip.width(), complete: () => this.form.submit()})
  }

  submitUndo () {
    this.answered = true
    this.undo.attr('value', 'true')
    this.$no.height(0)
    this.$yes.height(0)
    this.$skip.width(0)
    this.$undo.animate({width: '100%'}, {duration: 250, start: this.$undo.width(), complete: () => this.form.submit()})
  }

  reset () {
    this.$yes.animate({height: '0'}, 100)
    this.$no.animate({height: '0'}, 100)
    this.$skip.animate({width: '0'}, 100)
    this.$undo.animate({width: '0'}, 100)
  }

  swipeStatus (event, phase, direction, distance) {
    if (phase === 'move') {
      if (direction === 'down') {
        this.$no.css('height', distance * 1.5)
      } else if (direction === 'up') {
        this.$yes.css('height', distance * 1.5)
      } else if (direction === 'left') {
        this.$skip.css('left', $(window).width() - distance * 1.5)
        this.$skip.css('width', distance * 1.5)
      } else if (direction === 'right') {
        this.$undo.css('width', distance * 1.5)
      }
    } else if (phase === 'cancel') {
      this.$yes.height(0)
      this.$no.height(0)
      this.$skip.width(0)
      this.$undo.width(0)
    } else if (phase === 'end') {
      if ((direction === 'down') && (distance > (window.innerHeight / 3))) {
        this.submitNo()
      } else if ((direction === 'up') && (distance > (window.innerHeight / 3))) {
        this.submitYes()
      } else if ((direction === 'left') && (distance > (window.innerWidth / 3)) && this.userCanSkip) {
        this.submitSkip()
      } else if ((direction === 'right') && (distance > (window.innerWidth / 3))) {
        this.submitUndo()
      } else {
        this.reset()
      }
    }
    event.preventDefault()
  }
}
