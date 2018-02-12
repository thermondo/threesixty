const $ = window.$
class Question {
  constructor () {
    this.answered = false
    this.submitNo = this.submitNo.bind(this)
    this.submitYes = this.submitYes.bind(this)
    this.reset = this.reset.bind(this)
    this.swipeStatus = this.swipeStatus.bind(this)
    this.$yes = $('.yes')
    this.checkbox = $('input[type="checkbox"]')
    this.form = $('form')[0]
    this.$no = $('.no')
    this.$body = $('.question-wrapper')
    this.$body.swipe(this)
    $(document).on('keydown', e => {
      if (!$('#search:focus').length) {
        if (!this.answered) {
          if (e.keyCode === 38) {  // up
            this.submitYes()
            return false
          }

          if (e.keyCode === 40) {  // down
            this.submitNo()
            return false
          }
        }
      }
    })
  }

  submitNo () {
    this.answered = true
    this.checkbox.attr('checked', false)
    this.$yes.height(0)
    this.$no.animate({height: '100%'}, {duration: 250, start: this.$no.height(), complete: () => this.form.submit()})
  }

  submitYes () {
    this.answered = true
    this.checkbox.attr('checked', true)
    this.$no.height(0)
    this.$yes.animate({height: '100%'}, {duration: 250, start: this.$yes.height(), complete: () => this.form.submit()})
  }

  reset () {
    this.$yes.animate({height: '0'}, 100)
    this.$no.animate({height: '0'}, 100)
  }

  swipeStatus (event, phase, direction, distance) {
    if (phase === 'move') {
      if (direction === 'down') {
        this.$no.css('height', distance * 1.5)
      } else if (direction === 'up') {
        this.$yes.css('height', distance * 1.5)
      }
    } else if (phase === 'cancel') {
      this.$yes.height(0)
      this.$no.height(0)
    } else if (phase === 'end') {
      if ((direction === 'down') && (distance > (window.innerHeight / 3))) {
        this.submitNo()
      } else if ((direction === 'up') && (distance > (window.innerHeight / 3))) {
        this.submitYes()
      } else {
        this.reset()
      }
    }
    event.preventDefault()
  }
}

$(() => { window.question = new Question() })
