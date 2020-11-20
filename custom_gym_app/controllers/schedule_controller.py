# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from collections import OrderedDict
from odoo.http import request


class PortalSchedule(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        if 'schedule_count' in counters:
            logged_in_user = request.env['res.users'].browse([request.session.uid])

            schedule_count = 0

            if logged_in_user.partner_id.gym_type:
                if logged_in_user.partner_id.gym_type == 'trainer':
                    schedule_count = request.env['planning.slot'].search_count([('employee_id.name', '=', logged_in_user.name)])
                elif logged_in_user.partner_id.gym_type == 'member':
                    schedule_count = request.env['planning.slot'].search_count([])
            else:
                schedule_count = request.env['planning.slot'].search_count([])

            values['schedule_count'] = schedule_count

        return values

    def _schedule_get_page_view_values(self, schedule, access_token, **kwargs):
        values = {
                    'page_name': 'schedule',
                    'schedule': schedule,
                 }
        return self._get_page_view_values(schedule, access_token, values, 'my_schedule_history', False, **kwargs)

    @http.route(['/my/schedule', '/my/schedule/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_schedule(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        Schedule = request.env['planning.slot']

        logged_in_user = request.env['res.users'].browse([request.session.uid])

        schedule_count = 0

        if logged_in_user.partner_id.gym_type:
            if logged_in_user.partner_id.gym_type == 'trainer':
                schedule_count = Schedule.search_count(['|', ('user_id.name', '=', logged_in_user.name), ('employee_id.name', '=', logged_in_user.name)])
            elif logged_in_user.partner_id.gym_type == 'member':
                schedule_count = Schedule.search_count([])
        else:
            schedule_count = Schedule.search_count([])

        pager = portal_pager(
                                url="/my/schedule",
                                url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
                                total=schedule_count,
                                page=page,
                                step=self._items_per_page
                            )

        schedules = None

        if logged_in_user.partner_id.gym_type:
            if logged_in_user.partner_id.gym_type == 'trainer':
                schedules = Schedule.sudo().search(['|', ('user_id.name', '=', logged_in_user.name), ('employee_id.name', '=', logged_in_user.name)], order=None, limit=self._items_per_page, offset=pager['offset'])
            elif logged_in_user.partner_id.gym_type == 'member':
                schedules = Schedule.sudo().search([], order=None, limit=self._items_per_page, offset=pager['offset'])
        else:
            schedules = Schedule.sudo().search([], order=None, limit=self._items_per_page, offset=pager['offset'])

        request.session['my_schedule_history'] = schedules.ids[:100]

        values.update({
                            'date': date_begin,
                            'schedules': schedules,
                            'page_name': 'schedule',
                            'pager': pager,
                            'default_url': '/my/schedule',
                            'sortby': sortby,
                            'filterby': filterby,
                     })
        return request.render("custom_gym_app.portal_my_schedule", values)

    @http.route(['/my/schedule/<int:schedule_id>'], type='http', auth="public", website=True)
    def portal_my_schedule_detail(self, schedule_id, access_token=None, report_type=None, download=False, **kw):
        try:
            schedule_sudo = self._document_check_access('planning.slot', schedule_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=schedule_sudo, report_type=report_type, report_ref='custom_gym_app.report_schedule_card', download=download)

        values = self._schedule_get_page_view_values(schedule_sudo, access_token, **kw)

        return request.render("custom_gym_app.portal_my_schedule_page", values)
