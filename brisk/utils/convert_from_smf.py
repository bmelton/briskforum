import hashlib
from string import lower
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from djangochat import settings
from django.conf import settings
from userprofile.models import Profile
from django.db import connection
from models import Category, Forum, Topic, Post, SMFConversion
from poll.models import Poll, Choice, Log
from django.contrib.auth.models import User
from datetime import datetime
import time
from postmarkup import render_bbcode
from privatemessages.models import Message

class ConvertSMF:
    forum_list = (58, 137, 176, 189, 178, 180, 167, 174, 179, 96, 97, 121, 99, 154, 73, 171, 153, 7, 160, 98, 2, 152, 166, 173)

    def fix_epoch(self, input):
        if input == 0:
            return None
        else:
            return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(input)) 

    def clean(self, input):
        input   = input.replace("<br />", "\r\n")
        input   = input.replace("&quot;", "\"")
        input   = input.replace("&#039;", "'")
        input   = input.replace("&nbsp;", " ")
        return input

    def clear_polls(self):
        Poll.objects.all().delete()
        Choice.objects.all().delete()

    def convert_polls(self):
        self.clear_polls()

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM smf_polls")
        rows = cursor.fetchall()

        for row in rows:
            try:
                profile                 = Profile.objects.get(old_user_id=row[7])
                try:
                    poll = Poll()
                    poll.old_poll_id        = row[0]
                    poll.user               = profile.user
                    poll.username           = row[8]
                    poll.question           = row[1]
                    if row[2] == 1:
                        poll.locked = True

                    poll.expires_on = self.fix_epoch(row[4])
                    if row[5] == 0:
                        poll.hide_results_until_vote = False

                    if row[6] == 0:
                        poll.allow_changing_votes = False
                    poll.allow_changing_votes = False
                    if row[9] == 1:
                        poll.allow_changing_votes = True
                    poll.hide_results_until_expored = False
                    poll.save()
                except Exception, e:
                    print "Could not save poll: %s" % (str(e))
            except Profile.DoesNotExist, e:
                pass

    def convert_poll_choices(self):
        cursor = connection.cursor();
        cursor.execute("SELECT * FROM smf_poll_choices");
        rows = cursor.fetchall()

        for row in rows:
            try: 
                poll = Poll.objects.get(old_poll_id=row[0])
                try:
                    choice = Choice()
                    choice.poll = poll
                    choice.old_choice_id = row[1]
                    choice.label = row[2]
                    choice.votes = row[3]
                    choice.save()

                except Exception, e:
                    print str(e)
            except Poll.DoesNotExist, e:
                print str(e)

    def convert_poll_logs(self):
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM smf_log_polls");
        rows = cursor.fetchall()
        for row in rows:
            try:
                poll    = Poll.objects.get(old_poll_id=row[0])
                profile = Profile.objects.get(old_user_id=row[1])
                choice  = Choice.objects.get(old_choice_id=row[2], poll=poll)

                log = Log()
                log.user = profile.user
                log.username = profile.user.username
                log.poll = poll
                log.choice = choice
                log.save()
            except Exception, e:
                print str(e);

    def convert_all_polls(self):
        self.clear_polls()
        self.convert_polls()
        self.convert_poll_choices()
        self.convert_poll_logs()
        print "Finished converting polls"

    def markup(self, input):
        input   = render_bbcode(input)
        return input

    def calculate_time(self, start_time, end_time):
        input = end_time-start_time
        if input < 60:
            print "Completed: Program ran in %d seconds" % input
            return "%d seconds" % input
        else:
            print "Completed: Program ran in %d minutes" % (input/60)
            return "%d minutes" % (input/60)

    def check_users(self):
        start_time = time.time()
        emails = []
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM smf_members;")
        rows = cursor.fetchall()
        for row in rows:
            try: 
                user = User.objects.get(username=row[1])
            except User.DoesNotExist:
                try:
                    print "User %s does not exist. Creating" % row[1]
                    user = User.objects.create_user(row[1], row[12])
                    user.set_unusable_password()
                    user.save()

                    profile                 = Profile()
                    profile.user            = user
                    profile.personal_text   = row[13]
                    profile.location        = row[18]
                    profile.old_user_id     = row[0]
                    profile.website         = row[17]
                    profile.title           = row[32]
                    profile.save()
                except Exception, e:
                    print "Could not create user %s, %s" % (row[1], str(e))
        self.calculate_time(start_time, time.time())


    def convert_users(self):
        start_time = time.time()
        emails = []
        users = User.objects.values('email')
        for user in users:
            emails.append(user["email"])

        print emails

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM smf_members;")
        rows = cursor.fetchall()

        for row in rows:
            old_id              = row[0]
            username            = row[1]
            date_registered     = row[2]
            post_count          = row[3]
            last_login          = row[6]
            email               = row[12]
            personal_text       = row[13]
            gender              = row[14]
            website             = row[17]
            location            = row[18]

            if email in emails:
                user = User.objects.get(email=row[12])
                profile, created = Profile.objects.get_or_create(user=user)
                if created:
                    profile.save()
            else:
                try:
                    user = User.objects.create_user(row[1], row[12])
                    user.set_unusable_password()
                    user.save()

                    profile                 = Profile()
                    profile.user            = user
                    profile.personal_text   = row[13]
                    profile.location        = row[18]
                    profile.old_user_id     = row[0]
                    profile.website         = row[17]
                    profile.title           = row[32]
                    profile.save()
                except Exception, e:
                    with open("conversion_errors.log", "a") as myfile:
                        myfile.write("%s \r\n %s\r\n\r\n" % (row[1], str(e)))

        self.calculate_time(start_time, time.time())

    def convert_categories(self):
        start_time = time.time()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM smf_categories;")
        rows = cursor.fetchall()

        for row in rows:
            category = Category()

            category.old_category_id    = row[0]
            category.name               = row[2]
            category.position           = row[1]
            category.active             = True
            category.save()

        self.calculate_time(start_time, time.time())

    def convert_forums(self):
        start_time = time.time()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM smf_boards;")
        rows = cursor.fetchall()

        for row in rows:
            forum = Forum()
            category = Category.objects.get(old_category_id=row[1])

            forum.category              = category
            forum.old_forum_id          = row[0]
            forum.position              = row[4]
            forum.name                  = row[10]
            forum.description           = row[11]
            forum.active                = True
            forum.save()

        self.calculate_time(start_time, time.time())

    def clear_messages(self):
        Message.objects.all().delete()

    def clear_posts(self, board_id):
        Post.objects.filter(old_forum_id=board_id).delete()

    def clear_topics(self, board_id):
        Topic.objects.filter(forum__old_forum_id=board_id).delete()

    def convert_topics(self, board_id=181):
        start_time = time.time()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM smf_topics WHERE id_board=%s;" % board_id)
        rows = cursor.fetchall()
        for row in rows:
            try:
                try: 
                    profile = Profile.objects.get(old_user_id=row[5])
                except Profile.DoesNotExist, e:
                    if not row[5] == 0:
                        print "Profile does not exist. No big. -- %s" % row[5]
                    profile = None
                forum = Forum.objects.get(old_forum_id=row[2])
                cursor2 = connection.cursor()
                cursor2.execute("select subject FROM smf_messages WHERE id_topic=%s ORDER BY id_msg ASC LIMIT 1" % row[0])
                message = cursor2.fetchone()
                sticky = False
                if row[1] == 1:
                    sticky = True
                topic                       = Topic()
                if profile == None:
                    topic.user                  = None
                else:
                    topic.user              = profile.user
                topic.old_poll_id           = row[7]
                topic.forum                 = forum
                topic.name                  = message[0]
                topic.old_topic_id          = row[0]
                topic.sticky                = sticky
                topic.forum                 = Forum.objects.get(old_forum_id=row[2])
                topic.updated               = datetime.now()
                topic.views                 = row[9]
                topic.save()
            except Exception, e:
                with open("conversion_errors.log", "a") as myfile:
                    myfile.write("%s - %s \r\n %s\r\n\r\n" % (row[0], row[1], str(e)))
        self.calculate_time(start_time, time.time())

    def post_convert_topics(self, board_id):
        forum = Forum.objects.get(old_forum_id=board_id)

        start_time = time.time()
        for topic in Topic.objects.filter(forum=forum):
            if topic.get_body.user:
                topic.user              = topic.get_body.user
                topic.legacy_username   = topic.get_body.user.username
            else:
                topic.legacy_username   = topic.get_body.legacy_username
            topic.created               = topic.get_body.created
            if topic.get_body.updated:
                topic.modified          = topic.get_body.updated
            topic.save()
        
        self.calculate_time(start_time, time.time())

    def convert_posts(self, board_id=181):
        start_time = time.time()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM smf_messages WHERE id_board=%d ORDER BY id_msg ASC" % board_id)
        rows = cursor.fetchall()
        for row in rows:
            try: 
                try:
                    profile = Profile.objects.get(old_user_id=row[4])
                except Profile.DoesNotExist, e:
                    if not row[4] == 0:
                        print "Profile does not exist for %s" % (row[4])
                    profile = None

                try: 
                    topic = Topic.objects.get(old_topic_id=row[1])
                except Topic.DoesNotExist, e:
                    print "Topic %s does not exist" % (row[1])

                post = Post()
                post.topic          = topic
                post.old_post_id    = row[0]
                if profile == None:
                    post.user           = None
                else:
                    post.user           = profile.user
                post.legacy_username= row[7]
                post.created        = self.fix_epoch(row[3])
                post.updated        = self.fix_epoch(row[11])
                post.subject        = row[6]
                post.body           = self.clean(row[13])
                post.body_html      = self.markup(self.clean(row[13]))
                post.user_ip        = row[9]
                post.save()
                post.topic.save()

            except Exception, e:
                """
                with open("conversion_errors.log", "a") as myfile:
                    myfile.write("%s - %s \r\n %s\r\n\r\n" % (row[0], row[1], str(e)))
                """
                print "Other exception: %s" % (str(e))

        self.calculate_time(start_time, time.time())

    def convert_full(self, board_id):
        self.start_conversion(board_id)
        self.clear_topics(board_id)
        forum = Forum.objects.get(old_forum_id=board_id)
        self.convert_topics(board_id)
        self.convert_posts(board_id)
        self.post_convert_topics(board_id)
        # self.clear_posts(forum.pk)
        self.finish_conversion(board_id)
        return None

    def start_conversion(self, board_id):
        try:
            start_time              = datetime.now()
            forum                   = Forum.objects.get(old_forum_id=board_id)

            conversion              = SMFConversion()
            conversion.active       = True
            conversion.forum        = board_id
            conversion.name         = forum.name
            conversion.has_begun    = True
            conversion.begun        = start_time
            conversion.save()
            print "Started conversion"
            return True
        except Exception, e:
            print str(e)
            return False

    def finish_conversion(self, board_id):
        try:
            end_time                = datetime.now()
            conversion              = SMFConversion.objects.get(forum=board_id)
            conversion.has_finished = True
            conversion.finished     = datetime.now()
            conversion.active       = False
            conversion.save()
            return True
        except Exception, e:
            print str(e)
            return False

    def convert_everything(self):
        start_time = time.time()
        self.convert_pms()

    def convert_pms(self):
        start_time = time.time()
        self.clear_messages()

        cursor = connection.cursor()
        # cursor.execute("SELECT * FROM smf_personal_messages ORDER BY id_pm ASC")
        cursor.execute(" SELECT f.id_pm, f.deleted_by_sender, f.id_member_from, f.from_name, \
            f.msgtime, f.subject, f.body, f.from_name, t.id_member, t.is_read, t.deleted FROM \
            smf_personal_messages AS f INNER JOIN smf_pm_recipients AS t ON f.id_pm = t.id_pm;")
        rows = cursor.fetchall()
        for row in rows:
            try: 
                message = Message()
                try:
                    sender = Profile.objects.get(old_user_id=row[2])
                    message.sender = sender.user
                except Profile.DoesNotExist, e:
                    if not row[2] == 0:
                        print "Profile does not exist for %s" % (row[2])
                        sender = None
                except Exception, e:
                    print "Sender %s does not exist." % (row[2])
                    sender = None


                try:
                    recipient = Profile.objects.get(old_user_id=row[8])
                    message.recipient = recipient.user
                except Profile.DoesNotExist, e:
                    try: 
                        message.recipient = User.objects.get(username=row[7])
                    except User.DoesNotExist, e:
                        message.recipient_name = row[7]
                        message.recipient = None
                        print "Recipient %s could not be found." % row[8]
                except Exception, e:
                    print "Old user id: %s" % (row[8])
                    message.recipient = None

                message.read = False
                if row[9] == 1:
                    message.read = True
        
                message.deleted = False
                if row[10] == 1:
                    message.deleted = True

                message
                message.created = self.fix_epoch(row[4])
                message.subject = row[5]
                message.message = self.clean(row[6])
                message.save()
            except Exception, e:
                print str(e)

        self.calculate_time(start_time, time.time())

    def do_all(self):
        # This gets all the polls -- has to be done before forum topics.
        j.convert_all_polls()

        # This gets all the forum objects.  Will take a long damn time.
        SMFConversion.objects.all().delete()
        for i in self.forum_list:
            self.convert_full(i)
