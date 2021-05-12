# File to define routes for possible actions of the app


from flask import session, redirect, url_for, render_template, request
from . import main
from .forms import LoginForm
import flask
from .models import db, Hotels, Brief_explanations, Aspects_hotels, Comments, Preferences, Feature_category, Reviews, Actions, Hotel_user_rank
import logging
import flask
from flask import Flask, render_template, session
from flask import request
import pandas as pd
import traceback
import requests
import os

logger = logging.getLogger('app')
handler = logging.FileHandler('app.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

top_n = 10
her_username = 'dms_gui'
her_password = 'h6hsk+llgd8c5hd6bas'
intention_endpoint = 'https://conversational-rs.herokuapp.com/NLU/GetIntention/'
reply_endpoint = 'https://conversational-rs.herokuapp.com/ExplainableRS/GetReply/'
log_endpoint = 'https://conversational-rs.herokuapp.com/ExplainableRS/Log/'

@main.route('/', methods=['GET', 'POST'])
def index():
    """Login form to enter a room."""
    form = LoginForm()

    try:
        if True: #request.method != 'POST':
            if not flask.globals.session.get("hotel") is None:  # session already set
                session['hotel'] = request.args.get('hotel', None)  # set only hotel
            else:
                flask.globals.session['hotel'] = request.args.get('hotel', None)
            if not request.args.get('actionslog', None) is None:
                if request.args.get('actionslog', None) == 'a158':  # special code for check actionslog
                    actions = db.session.query(Actions.action_type, Actions.page, Actions.feature, Actions.description,
                                               Actions.date, Actions.userID, Actions.condition, Actions.workerID,
                                               Actions.hotelID, Actions.reviewID). \
                        filter(Actions.back == 0).order_by(desc(Actions.date)).all()
                    return render_template('actionslog.html', actions=actions)
            try:
                # validation initial set of variables
                if (flask.globals.session.get("condition") is None) | (flask.globals.session.get("workerID") is None) | (flask.globals.session.get("userID") is None):
                    if (request.args.get('condition', None) is None) | (request.args.get('workerID', None) is None) | (request.args.get('features', None) is None):
                        return render_template('no_params.html')


                if not request.args.get('book', None) is None: # if user clicked to book hotel
                    if request.args.get('book', None) == 'yes':
                        hotelID=''
                        if not request.args.get('hotelID', None) is None:
                            hotelID = request.args.get('hotelID', None)
                        try:
                            new_action = Actions(page='index', action_type='book', description='',
                                                 userID=flask.globals.session['userID'],
                                                 condition=flask.globals.session['condition'],
                                                 workerID=flask.globals.session['workerID'], hotelID=hotelID)

                            db.session.add(new_action)
                            db.session.commit()
                            db.session.close()
                            return render_template('end_page.html')
                        except Exception as e:
                            db.session.rollback()
                            db.session.close()
                            print('Error logging action index page: ' + str(e) + ', workerID:'+flask.globals.session['workerID'])
                            logger.error('Error logging action index page: ' + str(e) + ', workerID:'+flask.globals.session['workerID'])

                first_in = False
                # set variables in session
                if flask.globals.session.get("condition") is None:  # there's no variables in session yet
                    if not request.args.get('condition', None) is None:  # if we receive the condition in the url (first call)
                        flask.globals.session['condition'] = request.args.get('condition', None)  # then set the variable
                        first_in = True
                else:
                    if not request.args.get('condition', None) is None:
                        if flask.globals.session.get("condition") != request.args.get('condition',
                                                                                      None):  # new condition sent in request
                            flask.globals.session['condition'] = request.args.get('condition', None)

                if flask.globals.session.get("workerID") is None:  # there's no variables in session yet
                    if not request.args.get('workerID', None) is None:  # if we receive the workerID in the url (first call)
                        flask.globals.session['workerID'] = request.args.get('workerID', None)  # then set the variable

                if flask.globals.session.get("userID") is None:  # there's no variables in session yet
                    if not request.args.get('features', None) is None:  # if we receive the features in the url (first call)
                        try:
                            # This section is used to infer user with similar preferences to our participant
                            survey = request.args.get('features', None)
                            # survey = survey.split('-')

                            aspects_all = ['facilities', 'staff', 'room', 'bathroom', 'location', 'price', 'ambience',
                                           'food', 'comfort', 'checking']
                            #survey = '1a-9a2a-9a3a4a5a-9a-9' # this is an example of type of input received
                            survey = survey.split('a')
                            aspects_survey_str = []
                            for i in range(1, 6):
                                aspects_survey_str.append(aspects_all[survey.index(str(i))])
                            survey = aspects_survey_str
                            print('features from survey: ' + str(survey) + ', workerID:'+flask.globals.session['workerID'])
                            logger.info('features from survey: ' + str(survey) + ', workerID:'+flask.globals.session['workerID'])
                            preferences = Preferences.query.all()

                            common_aspects = pd.DataFrame(columns=['userID', 'common'])
                            for pref in preferences:
                                count_occ = 0
                                for i in survey:
                                    if i in [pref.pref_0, pref.pref_1, pref.pref_2, pref.pref_3, pref.pref_4]: count_occ += 1
                                common_aspects = common_aspects.append(pd.DataFrame({'userID': [pref.userID], 'common': [count_occ]}))

                            max_occ = common_aspects['common'].max()
                            common_aspects = common_aspects[common_aspects.common == max_occ]
                            most_similar = 0
                            for idx, row in common_aspects.iterrows():
                                preferences = Preferences.query.filter(Preferences.userID == row.userID).all()
                                if pref.pref_0 == survey[0]:
                                    most_similar = row.userID # the one with the same first preference

                            if most_similar == 0:
                                for idx, row in common_aspects.iterrows():
                                    if pref.pref_1 == survey[0]:
                                        most_similar = row.userID # the one with the same second preference
                            if most_similar == 0:
                                most_similar = common_aspects.iloc[0,:].userID # first of the most commonalities

                        except Exception as e:
                            print('Error Processing user preferences: ' + str(e) + ', workerID:'+flask.globals.session['workerID'])
                            logger.error('Error Processing user preferences, we will set the default user: ' + str(e) + ', workerID:'+flask.globals.session['workerID'])
                            most_similar = 160 # a default user

                        print("most_similar:" + str(most_similar))
                        userID = most_similar
                        flask.globals.session['userID'] = userID
                    else:
                        userID = 160 # a default user
                        flask.globals.session['userID'] = userID
                        logger.info('We havent received features, so, we will set the default user: ' + str(e))

                # log action
                back = 0
                if not request.args.get('back', None) is None: back = 1
                try:
                    new_action = Actions(page='index', action_type='load', description='',
                                        userID=flask.globals.session['userID'], condition=flask.globals.session['condition'],
                                        workerID=flask.globals.session['workerID'], back=back)

                    db.session.add(new_action)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print('Error logging action index page: ' + str(e) + ', workerID:'+flask.globals.session['workerID'])
                    logger.error('Error logging action index page: ' + str(e) + ', workerID:'+flask.globals.session['workerID'])

                userID=flask.globals.session['userID']
                hotels = db.session.query(Hotels.hotelID, Brief_explanations.hotelID, Hotels.name, Hotels.num_reviews,
                                           Brief_explanations.explanation, Hotels.price, Hotels.stars_file). \
                                            outerjoin(Hotel_user_rank, Hotels.hotelID == Hotel_user_rank.hotelID). \
                                            outerjoin(Brief_explanations, Hotels.hotelID == Brief_explanations.hotelID). \
                                            filter(Hotel_user_rank.userID == userID). \
                                            filter(Brief_explanations.userID == userID). \
                                            filter(Hotel_user_rank.rank <= top_n). \
                                            order_by(Hotel_user_rank.rank). \
                                            all()

                # Process question
                question = ''
                try:
                    question = form.question.data
                    count_qs = form.count_qs.data
                    intention_last = form.intention_last.data
                    question_last = form.question_last.data
                    reply_last = form.reply_last.data

                    if (count_qs is None) | (count_qs == ''):
                        count_qs = 0
                    reply = ''
                    perception = form.perception.data
                    #print('perception: '+ perception)
                    #print('count_qs: ' + str(count_qs))

                    user = 'non_received'
                    if flask.globals.session.get("workerID") is None:  # there's no variables in session yet
                        if not request.args.get('workerID', None) is None:  # if we receive the workerID in the url (first call)
                            user = request.args.get('workerID', None)  # then set the variable
                    else:
                        user = flask.globals.session.get("workerID")

                    # if question == 'q':
                    #     reply = 'r'
                    if (not question is None) &  (not question == ''):
                        form.count_qs.data = str(int(count_qs) + 1)
                        form.question_last.data = question
                        form.submit.label.text = 'Rate reply'
                        response = requests.get(intention_endpoint, json={"sentence": question},
                                                auth=(her_username, her_password))
                        # print(response.status_code)
                        if not response:  # or not 'hotels' in request.json:
                            print('error 400')
                        if 'error' in response.json():
                            print("Error getting intention:" + response.json().get("error"))

                        if (not response is None) & (not response.json() is None):
                            aspect = assessment = comparison = detail = scope = ''
                            entities = []
                            if 'aspect' in response.json():
                                aspect = response.json().get('aspect')
                            if 'entities' in response.json():
                                entities = response.json().get('entities')
                            else:
                                entities = []
                            if 'intention' in response.json():
                                intention = response.json().get('intention')
                                assessment = intention.get('assessment')
                                comparison = intention.get('comparison')
                                detail = intention.get('detail')
                                scope = intention.get('scope')
                                form.intention_last.data = scope + ';' + comparison + ';' + assessment + ';' + detail + ';' + aspect + ';' + str(entities)
                                # print(aspect +'-'+ assessment +'-'+ comparison +'-'+ detail +'-'+ scope)

                                json_req = {"userID": user, "similar_user": userID, "sentence": question, "aspect": aspect,
                                            "entities": entities, "preferences": [],
                                            "intention": {"scope": scope, "comparison": comparison,"assessment": assessment,
                                                          "detail": detail}}
                                #print(json_req)
                                response = requests.get(reply_endpoint, json=json_req,auth=(her_username, her_password))
                                #print(response.status_code)
                                if not response:  # or not 'hotels' in request.json:
                                    print('error 400')
                                if 'error' in response.json():
                                    print("Error getting reply:" + response.json().get("error"))
                                if 'error_description' in response.json():
                                    reply = response.json().get("error_description")
                                #print(response)
                                if (not response is None) & (not response.json() is None):
                                    if 'reply' in response.json():
                                        reply = response.json().get('reply')
                                #print(reply)
                                form.reply_last.data = reply
                    if (not perception is None) & (not perception == 'None'):
                        message = 'REPLYRATING: ' + str(user) + ';' + str(userID) + ';' + str(int(count_qs)) + ';' + question_last + ';' + reply_last + ';' + str(perception) + ';' + intention_last
                        print('message: '+message)
                        json_req = {"message": message}
                        response = requests.post(log_endpoint, json=json_req, auth=(her_username, her_password))

                        if not response:  # or not 'hotels' in request.json:
                            print('error 400')
                        elif 'error' in response.json():
                            print(response.json().get("error"))

                        form.question.data = ''
                        form.submit.label.text = ' '

                except Exception as e:
                    print('Error:')
                    print(e)
                    traceback.print_exc()
                # hotels = session.query(Hotels).all()
                #return render_template('index.html', hotels=hotels, form=form, reply=reply, count_qs=str(count_qs+1), user_q = question)
                return render_template('index.html', hotels=hotels, form=form, reply=reply, user_q = question, count_qs=str(int(count_qs) + 1))

            except Exception as e:

                print('Error loading index page: ' + str(e) + ', workerID:'+flask.globals.session['workerID'])
                logger.error('Error loading index page: ' + str(e) + ', workerID:'+flask.globals.session['workerID'])
                return render_template('error.html')
    except:
        session.rollback()
        print('Error loading index page: ' + str(e) + ', workerID:' + flask.globals.session['workerID'])
        logger.error('Error loading index page: ' + str(e) + ', workerID:' + flask.globals.session['workerID'])
        return render_template('error.html')
    finally:
        print("I will close the session")
        db.session.close()

@main.route('/hotel_general/<int:hotelID>', methods=['GET', 'POST'])
def hotel_general(hotelID):
    try:
        if request.method != 'POST':
            try:
                #db_session
                hotel_revs = db.session.query(Hotels.hotelID, Reviews.hotelID, Hotels.name, Hotels.num_reviews,
                                              Hotels.stars_file, Hotels.score, Hotels.price,
                                              Reviews.author, Reviews.score, Reviews.review_text). \
                    outerjoin(Reviews, Hotels.hotelID == Reviews.hotelID). \
                    filter(Hotels.hotelID == hotelID).all()
                try:
                    new_action = Actions(page='hotel_general', action_type='load', description='', hotelID=hotelID,
                                         userID=flask.globals.session['userID'],
                                         condition=flask.globals.session['condition'],
                                         workerID=flask.globals.session['workerID'], back=0)

                    db.session.add(new_action)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print('Error logging action hotel general page: ' + str(e) + ', workerID:'+flask.globals.session['workerID'])
                    logger.error('Error logging action hotel general page: ' + str(e) + ', workerID:'+flask.globals.session['workerID'])


                return render_template('hotel_general.html', hotel_revs=hotel_revs)
            except Exception as e:
                print('Error loading comments page: ' + str(e) + ', workerID:'+flask.globals.session['workerID'])
                traceback.print_exc()
                logger.error('Error loading comments page: ' + str(e) + ', workerID:'+flask.globals.session['workerID'])
                return render_template('error.html')
        return ""
    except:
        session.rollback()
        print('Error loading index page: ' + str(e) + ', workerID:' + flask.globals.session['workerID'])
        logger.error('Error loading index page: ' + str(e) + ', workerID:' + flask.globals.session['workerID'])
        return render_template('error.html')
    finally:
        print("I will close the session")
        db.session.close()



