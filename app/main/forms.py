# Basic form to login into chan

from flask_wtf import Form
from wtforms.fields import StringField, SubmitField, HiddenField, RadioField, SelectField
from wtforms.validators import Required


class LoginForm(Form):
    question = StringField('Question', validators=[Required()], render_kw={"placeholder": "Enter your question here ..."})
    #reply = HiddenField('Reply')
    #perception = RadioField('Label', choices=[('Strongly disagree','Disagree', 'Neutral', 'Agree', 'Strongly agree'),('1','2','3','4','5')])
    #perception = RadioField('Label', choices=[('1','Strongly disagree'),('2','Disagree')])
    perception = SelectField(u'Was this answer helpful?: ', choices=[('0', ' '),('1', 'Strongly disagree'), ('2', 'Disagree'), ('3', 'Neutral'), ('4', 'Agree'), ('5', 'Strongly agree')])
    count_qs = HiddenField("Count questions")
    intention_last = HiddenField("Intention")
    question_last = HiddenField("Question last")
    reply_last = HiddenField("Intention last")
    style = {'style': 'text-decoration:underline'}
    submit = SubmitField(' ', render_kw=style)

