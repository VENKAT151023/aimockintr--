import re

with open('applns.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_completion_block = """    if index >= len(questions):
        # All questions answered - score immediately and go straight
        # to the result screen (no extra waiting screen in between).
        answers = session.get('interview_answers', [])
        score, feedback = calculate_interview_score(answers)
        user = get_current_user()
        user.interview_complete = True
        user.final_score = score
        user.passed = score >= app.config['PASS_SCORE']
        user.meeting_live = False
        user.interview_date = datetime.utcnow()
        user.interview_feedback = '\\n'.join(feedback)
        if user.passed:
            user.company_message = "🎉 Congratulations! You have passed the LARA AI interview! Welcome to the team!"
        else:
            user.company_message = "😔 Thank you for attending. Your score was below the passing mark this time - keep practicing and you'll do better!"
        if 'interview_session_id' in session:
            existing_session = InterviewSession.query.filter_by(
                session_id=session['interview_session_id']
            ).first()
            if existing_session:
                existing_session.is_active = False
                existing_session.completed_at = datetime.utcnow()
                db.session.commit()
        db.session.commit()
        for idx, ans in enumerate(answers):
            interview_ans = InterviewAnswer(
                user_id=user.id,
                question_index=idx,
                question=ans.get('question', ''),
                answer=ans.get('answer', ''),
                score=score // len(answers) if answers else 0
            )
            db.session.add(interview_ans)
        db.session.commit()
        create_notification(user.id, 'Interview Completed', f'Your interview is complete. Score: {score}%', 'success' if user.passed else 'info')
        log_activity(user.id, 'interview_complete', f'Interview completed with score {score}')
        session.pop('interview_questions', None)
        session.pop('interview_index', None)
        session.pop('interview_answers', None)
        session.pop('camera_state', None)
        session.pop('interview_session_id', None)
        return redirect('/result')"""

new_completion_block = """    if index >= len(questions):
        # All questions answered - score immediately and go straight
        # to the result screen (no extra waiting screen in between).
        # Every DB write below is wrapped so that a failure in a
        # secondary write (answer log, notification, activity log)
        # can NEVER crash this page with a 500 - the person always
        # reaches the result screen with their score saved.
        answers = session.get('interview_answers', [])
        score, feedback = calculate_interview_score(answers)
        user = get_current_user()

        try:
            user.interview_complete = True
            user.final_score = score
            user.passed = score >= app.config['PASS_SCORE']
            user.meeting_live = False
            user.interview_date = datetime.utcnow()
            user.interview_feedback = '\\n'.join(feedback)
            if user.passed:
                user.company_message = "🎉 Congratulations! You have passed the LARA AI interview! Welcome to the team!"
            else:
                user.company_message = "😔 Thank you for attending. Your score was below the passing mark this time - keep practicing and you'll do better!"
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save interview result for user {user.id if user else '?'}: {e}")

        try:
            if 'interview_session_id' in session:
                existing_session = InterviewSession.query.filter_by(
                    session_id=session['interview_session_id']
                ).first()
                if existing_session:
                    existing_session.is_active = False
                    existing_session.completed_at = datetime.utcnow()
                    db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to close interview session: {e}")

        try:
            for idx, ans in enumerate(answers):
                interview_ans = InterviewAnswer(
                    user_id=user.id,
                    question_index=idx,
                    question=ans.get('question', ''),
                    answer=ans.get('answer', ''),
                    score=score // len(answers) if answers else 0
                )
                db.session.add(interview_ans)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save interview answers: {e}")

        try:
            create_notification(user.id, 'Interview Completed', f'Your interview is complete. Score: {score}%', 'success' if user.passed else 'info')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create completion notification: {e}")
        try:
            log_activity(user.id, 'interview_complete', f'Interview completed with score {score}')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to log interview_complete activity: {e}")

        session.pop('interview_questions', None)
        session.pop('interview_index', None)
        session.pop('interview_answers', None)
        session.pop('camera_state', None)
        session.pop('interview_session_id', None)
        return redirect('/result')"""

old_dashboard_actions = """    <div class="actions">
        <a href="/profile" class="action-btn"><div class="icon">👤</div><div class="label">Profile</div></a>
        <a href="/interview" class="action-btn"><div class="icon">🎙️</div><div class="label">Start Interview</div></a>
        <a href="/admin" class="action-btn" style="border-color:rgba(102,126,234,0.3);"><div class="icon">⚙️</div><div class="label">Admin Panel</div></a>
    </div>"""

new_dashboard_actions = """    <div class="actions">
        <a href="/profile" class="action-btn"><div class="icon">👤</div><div class="label">Profile</div></a>
        <a href="/interview" class="action-btn"><div class="icon">🎙️</div><div class="label">Start Interview</div></a>
        {% if user.interview_complete %}
        <a href="/result" class="action-btn" style="border-color:rgba(72,187,120,0.4);"><div class="icon">📊</div><div class="label">View Result</div></a>
        {% endif %}
        <a href="/admin" class="action-btn" style="border-color:rgba(102,126,234,0.3);"><div class="icon">⚙️</div><div class="label">Admin Panel</div></a>
    </div>"""

changed = 0
if old_completion_block in content:
    content = content.replace(old_completion_block, new_completion_block)
    changed += 1
else:
    print("NOT FOUND: completion block")

if old_dashboard_actions in content:
    content = content.replace(old_dashboard_actions, new_dashboard_actions)
    changed += 1
else:
    print("NOT FOUND: dashboard actions block")

with open('applns.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Done. {changed}/2 fixes applied.")