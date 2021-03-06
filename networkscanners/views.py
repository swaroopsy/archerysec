# -*- coding: utf-8 -*-
#                   _
#    /\            | |
#   /  \   _ __ ___| |__   ___ _ __ _   _
#  / /\ \ | '__/ __| '_ \ / _ \ '__| | | |
# / ____ \| | | (__| | | |  __/ |  | |_| |
# /_/    \_\_|  \___|_| |_|\___|_|   \__, |
#                                    __/ |
#                                   |___/
# Copyright (C) 2017-2018 ArcherySec
# This file is part of ArcherySec Project.

""" Author: Anand Tiwari """

from __future__ import unicode_literals

import datetime
import os
import threading
import time
import uuid
import xml.etree.ElementTree as ET

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response, HttpResponse
from django.utils import timezone

from archerysettings import save_settings
from networkscanners.models import scan_save_db, ov_scan_result_db
from projects.models import project_db
from scanners.scanner_parser.network_scanner import OpenVas_Parser
from scanners.scanner_plugin.network_scanner.openvas_plugin import OpenVAS_Plugin, vuln_an_id

openvas_data = os.getcwd() + '/' + 'apidata.json'

status = ""
name = ""
creation_time = ""
modification_time = ""
host = ""
port = ""
threat = ""
severity = ""
description = ""
page = ""
family = ""
cvss_base = ""
cve = ""
bid = ""
xref = ""
tags = ""
banner = ""


def index(request):
    """
    Function calling network base html.
    :param request:
    :return:
    """
    all_ip = scan_save_db.objects.all()

    return render(request, 'index.html', {'all_ip': all_ip})


def scan_status(request):
    """
    Check the network scan status.
    :param request:
    :return:
    """
    if request.method == 'POST':
        all_ip = scan_save_db.objects.all()
        scan_ip = request.POST.get('scan_id', )

    return render(request, 'index.html')


def scan_vul_details(request):
    """
    Get the Network scan vulnerability details.
    :param request:
    :return:
    """
    scanid = ""
    if request.method == 'GET':
        scanid = request.GET['scan_id']
    print "scansss", scanid

    if request.method == 'POST':
        vuln_id = request.POST.get('vuln_id')
        scan_id = request.POST.get('scan_id')
        false_positive = request.POST.get('false')

        ov_scan_result_db.objects.filter(
            scan_id=scan_id,
            vul_id=vuln_id).update(
            false_positive=false_positive)

        return HttpResponseRedirect(
            '/networkscanners/vul_details/?scan_id=%s' % scan_id)

    all_vuln = ov_scan_result_db.objects.filter(scan_id=scanid,
                                                false_positive='No').values('name', 'severity',
                                                                            'vuln_color',
                                                                            'threat', 'host',
                                                                            'port', 'vul_id').distinct()

    all_false_vul = ov_scan_result_db.objects.filter(scan_id=scanid,
                                                     false_positive='Yes').values('name', 'severity',
                                                                                  'vuln_color',
                                                                                  'threat', 'host',
                                                                                  'port', 'vul_id').distinct()
    print "zzzzzz", scanid
    return render(request,
                  'vul_details.html',
                  {'all_vuln': all_vuln,
                   'scan_id': scanid,
                   'all_false_vul': all_false_vul})


def openvas_scanner(scan_ip, project_id, sel_profile):
    """
    The function is launch the OpenVAS scans.
    :param scan_ip:
    :param project_id:
    :param sel_profile:
    :return:
    """
    openvas = OpenVAS_Plugin(scan_ip, project_id, sel_profile)
    scanner = openvas.connect()
    scan_id, target_id = openvas.scan_launch(scanner)
    date_time = timezone.now()
    save_all = scan_save_db(scan_id=str(scan_id),
                            project_id=str(project_id),
                            scan_ip=scan_ip,
                            target_id=str(target_id),
                            date_time=date_time)
    save_all.save()
    openvas.scan_status(scanner=scanner, scan_id=scan_id)
    time.sleep(5)
    vuln_an_id(scan_id=scan_id)

    return HttpResponse(status=201)


def launch_scan(request):
    """
    Function Trigger Network scans.
    :param request:
    :return:
    """
    all_ip = scan_save_db.objects.all()

    if request.method == 'POST':
        all_ip = scan_save_db.objects.all()
        scan_ip = request.POST.get('ip')
        project_id = request.POST.get('project_id')
        sel_profile = request.POST.get('scan_profile')
        ip = scan_ip.replace(" ", "")
        target_split = ip.split(',')
        split_length = target_split.__len__()
        print "split_lenght", split_length
        for i in range(0, split_length):
            target = target_split.__getitem__(i)
            print "Scan Launched IP:", target
            thread = threading.Thread(target=openvas_scanner, args=(target, project_id, sel_profile))
            thread.daemon = True
            thread.start()

    return render_to_response('vul_details.html',
                              {'all_ip': all_ip})


def scan_del(request):
    """
    Delete Network scans.
    :param request:
    :return:
    """

    if request.method == 'POST':
        scan_id = request.POST.get('scan_id')
        scan_item = str(scan_id)
        value = scan_item.replace(" ", "")
        value_split = value.split(',')
        split_length = value_split.__len__()
        # print "split_lenght", split_length
        for i in range(0, split_length):
            scan_id = value_split.__getitem__(i)
            scans = scan_save_db.objects.filter(scan_id=scan_id).order_by('scan_id')
            scans.delete()
            vuln_data = ov_scan_result_db.objects.filter(scan_id=scan_id)
            vuln_data.delete()

    return HttpResponseRedirect("/networkscanners/")


def ip_scan(request):
    """
    List all network scan IP's.
    :param request:
    :return:
    """
    all_scans = scan_save_db.objects.all()
    all_proj = project_db.objects.all()

    return render(request,
                  'ipscan.html',
                  {'all_scans': all_scans,
                   'all_proj': all_proj})


def ip_scan_table(request):
    """
    Network scan Table.
    :param request:
    :return:
    """
    all_scans = scan_save_db.objects.all()

    return render(request, 'ip_scan_table.html', {'all_scans': all_scans})


def openvas_details(request):
    """
    OpenVAS tool settings.
    :param request:
    :return:
    """
    save_openvas_setting = save_settings.SaveSettings(openvas_data)

    if request.method == 'POST':
        openvas_host = request.POST.get("scan_host")
        openvas_user = request.POST.get("openvas_user")
        openvas_password = request.POST.get("openvas_password")

        save_openvas_setting.openvas_settings(
            ipaddress=openvas_host,
            openvas_user=openvas_user,
            openvas_password=openvas_password,
        )

    messages.add_message(request,
                         messages.SUCCESS,
                         'Openvas Setting Updated ')

    return render(request, 'setting_form.html', )


def openvas_setting(request):
    """
    Calling OpenVAS setting page.
    :param request:
    :return:
    """
    return render(request,
                  'setting_form.html', )


def del_vuln(request):
    """
    Delete Network Vulnerability.
    :param request:
    :return:
    """
    if request.method == 'POST':
        vuln_id = request.POST.get("del_vuln")
        un_scanid = request.POST.get("scan_id")
        print "scan_iddd", un_scanid

        scan_item = str(vuln_id)
        value = scan_item.replace(" ", "")
        value_split = value.split(',')
        split_length = value_split.__len__()
        print "split_lenght", split_length
        for i in range(0, split_length):
            vuln_id = value_split.__getitem__(i)
            delete_vuln = ov_scan_result_db.objects.filter(vul_id=vuln_id)
            delete_vuln.delete()
        ov_all_vul = ov_scan_result_db.objects.filter(scan_id=un_scanid).order_by('scan_id')
        total_vul = len(ov_all_vul)
        total_high = len(ov_all_vul.filter(threat="High"))
        total_medium = len(ov_all_vul.filter(threat="Medium"))
        total_low = len(ov_all_vul.filter(threat="Low"))

        scan_save_db.objects.filter(scan_id=un_scanid) \
            .update(total_vul=total_vul,
                    high_total=total_high,
                    medium_total=total_medium,
                    low_total=total_low)
        messages.success(request, "Deleted vulnerability")

        return HttpResponseRedirect("/networkscanners/vul_details/?scan_id=%s" % un_scanid)


def edit_vuln(request):
    """
    Edit Network scan vulnerabilities.
    :param request:
    :return:
    """
    if request.method == 'POST':
        scan_id = request.POST.get("scan_id")
        vul_id = request.POST.get("vuln_id")
        name = request.POST.get("name")
        creation_time = request.POST.get("creation_time")
        modification_time = request.POST.get("modification_time")
        host = request.POST.get("host")
        port = request.POST.get("port")
        threat = request.POST.get("threat")
        severity = request.POST.get("severity")
        description = request.POST.get("description")
        family = request.POST.get("family")
        cvss_base = request.POST.get("cvss_base")
        cve = request.POST.get("cve")
        # bid = request.POST.get("bid")
        xref = request.POST.get("xref")
        tags = request.POST.get("tags")
        banner = request.POST.get("banner")

        ov_scan_result_db.objects.filter(vul_id=vul_id).update(name=name,
                                                               creation_time=creation_time,
                                                               modification_time=modification_time,
                                                               host=host, port=port,
                                                               threat=threat,
                                                               severity=severity,
                                                               description=description, family=family,
                                                               cvss_base=cvss_base, cve=cve,
                                                               xref=xref, tags=tags, banner=banner)

        messages.success(request, "Vulnerability Edited")

        return HttpResponseRedirect("/networkscanners/vul_details/?scan_id=%s" % scan_id)

    if request.method == 'GET':
        id_vul = request.GET['vuln_id']
    else:
        id_vul = ''
    edit_vul_dat = ov_scan_result_db.objects.filter(vul_id=id_vul).order_by('vul_id')

    return render(request, 'ov_edit_vuln_data.html', {'edit_vul_dat': edit_vul_dat})


def vuln_check(request):
    """
    Get the detailed vulnerability information.
    :param request:
    :return:
    """
    if request.method == 'GET':
        id_vul = request.GET['vuln_id']
    else:
        id_vul = ''
    vul_dat = ov_scan_result_db.objects.filter(vul_id=id_vul).order_by('vul_id')

    return render(request, 'ov_vuln_data.html', {'vul_dat': vul_dat})


def add_vuln(request):
    """
    Add network vulnerability.
    :param request:
    :return:
    """
    if request.method == 'GET':
        scan_id = request.GET['scan_id']
    else:
        scan_id = ''

    if request.method == 'POST':
        vuln_id = uuid.uuid4()
        scan_id = request.POST.get("scan_id")
        name = request.POST.get("name")
        creation_time = request.POST.get("creation_time")
        modification_time = request.POST.get("modification_time")
        host = request.POST.get("host")
        port = request.POST.get("port", )
        threat = request.POST.get("threat", )
        severity = request.POST.get("severity", )
        description = request.POST.get("description", )
        family = request.POST.get("family", )
        cvss_base = request.POST.get("cvss_base", )
        cve = request.POST.get("cve", )
        # bid = request.POST.get("bid")
        xref = request.POST.get("xref", )
        tags = request.POST.get("tags", )
        banner = request.POST.get("banner", )

        save_vuln = ov_scan_result_db(name=name,
                                      vul_id=vuln_id,
                                      scan_id=scan_id,
                                      creation_time=creation_time,
                                      modification_time=modification_time,
                                      host=host, port=port,
                                      threat=threat,
                                      severity=severity,
                                      description=description,
                                      family=family,
                                      cvss_base=cvss_base,
                                      cve=cve,
                                      xref=xref,
                                      tags=tags,
                                      banner=banner,
                                      false_positive='No',
                                      )
        save_vuln.save()

        messages.success(request, "Vulnerability Added")
        return HttpResponseRedirect("/networkscanners/vul_details/?scan_id=%s" % scan_id)

    return render(request, 'ov_add_vuln.html', {'scan_id': scan_id})


def OpenVas_xml_upload(request):
    """
    OpenVAS XML file upload.
    :param request:
    :return:
    """
    all_project = project_db.objects.all()
    if request.method == "POST":
        project_id = request.POST.get("project_id")
        scanner = request.POST.get("scanner")
        xml_file = request.FILES['xmlfile']
        scan_ip = request.POST.get("scan_url")
        scan_id = uuid.uuid4()
        scan_status = "100"
        if scanner == "openvas":
            date_time = datetime.datetime.now()
            scan_dump = scan_save_db(scan_ip=scan_ip,
                                     scan_id=scan_id,
                                     date_time=date_time,
                                     project_id=project_id,
                                     scan_status=scan_status)
            scan_dump.save()
            tree = ET.parse(xml_file)
            root_xml = tree.getroot()
            OpenVas_Parser.xml_parser(project_id=project_id,
                                      scan_id=scan_id,
                                      root=root_xml)
            return HttpResponseRedirect("/networkscanners/")

    return render(request,
                  'net_upload_xml.html',
                  {'all_project': all_project})
