/*
 * JS global do ERP.
 *
 * Plugins jQuery utilizados (carregados no base.html):
 *   1. jQuery Mask Plugin  -> máscaras de CPF/CNPJ, CNPJ e telefone nos formulários
 *   2. Bootbox.js          -> diálogos de confirmação (exclusão, baixa, cancelamento)
 *   3. DataTables          -> ordenação e busca rápida nas tabelas de extrato (.js-datatable)
 */
(function ($) {
    'use strict';

    // ---------- Utilitário: token CSRF ----------
    window.ERP = window.ERP || {};
    ERP.csrfToken = function () {
        return $('#csrf-global input[name=csrfmiddlewaretoken]').val();
    };

    // ---------- 1) jQuery Mask ----------
    function mascaraTelefone(val) {
        return val.replace(/\D/g, '').length === 11 ? '(00) 00000-0000' : '(00) 0000-00009';
    }

    function mascaraCpfCnpj(val) {
        return val.replace(/\D/g, '').length <= 11 ? '000.000.000-009' : '00.000.000/0000-00';
    }

    function aplicarMascaras() {
        $('#id_telefone').mask(mascaraTelefone, {
            onKeyPress: function (val, e, field, options) {
                field.mask(mascaraTelefone.apply({}, arguments), options);
            }
        });
        $('#id_cpf_cnpj').mask(mascaraCpfCnpj, {
            onKeyPress: function (val, e, field, options) {
                field.mask(mascaraCpfCnpj.apply({}, arguments), options);
            }
        });
        $('#id_cnpj').mask('00.000.000/0000-00');
        $('.js-mascara-dinheiro').mask('#.##0,00', { reverse: true });
    }

    // ---------- 2) Bootbox ----------
    bootbox.setDefaults({ centerVertical: true, backdrop: true });

    // Links de exclusão: confirma no modal e envia POST direto para a DeleteView.
    // Sem JS o link continua levando à página de confirmação (fallback).
    $(document).on('click', '.js-confirmar-exclusao', function (e) {
        e.preventDefault();
        var url = $(this).attr('href');
        var nome = $(this).data('nome') || 'este registro';
        bootbox.confirm({
            title: '<i class="ti ti-trash me-2"></i>Confirmar exclusão',
            message: 'Tem certeza que deseja excluir <strong>' + $('<span>').text(nome).html() +
                     '</strong>? Esta ação não pode ser desfeita.',
            buttons: {
                cancel: { label: 'Cancelar', className: 'btn-outline-green' },
                confirm: { label: '<i class="ti ti-trash me-1"></i>Excluir', className: 'btn-danger' }
            },
            callback: function (ok) {
                if (!ok) return;
                var $form = $('<form>', { method: 'post', action: url }).append(
                    $('<input>', { type: 'hidden', name: 'csrfmiddlewaretoken', value: ERP.csrfToken() })
                );
                $('body').append($form);
                $form.trigger('submit');
            }
        });
    });

    // Formulários de ação (baixar conta, cancelar venda/nota): data-mensagem="..."
    $(document).on('submit', 'form.js-confirmar', function (e) {
        var $form = $(this);
        if ($form.data('confirmado')) return true;
        e.preventDefault();
        bootbox.confirm({
            title: 'Confirmação',
            message: $('<span>').text($form.data('mensagem') || 'Confirmar esta ação?').html(),
            buttons: {
                cancel: { label: 'Voltar', className: 'btn-outline-green' },
                confirm: { label: 'Confirmar', className: 'btn-green' }
            },
            callback: function (ok) {
                if (ok) {
                    $form.data('confirmado', true);
                    $form.trigger('submit');
                }
            }
        });
    });

    // ---------- 3) DataTables ----------
    // A paginação continua no servidor (preserva filtros); o DataTables dá
    // ordenação por coluna e busca instantânea dentro da página.
    var idiomaPtBr = {
        search: 'Buscar nesta página:',
        zeroRecords: 'Nenhum registro encontrado',
        emptyTable: 'Nenhum registro',
        info: '_TOTAL_ registros',
        infoEmpty: '0 registros',
        infoFiltered: '(de _MAX_)'
    };

    function aplicarDataTables() {
        $('table.js-datatable').each(function () {
            var $t = $(this);
            // DataTables não aceita linhas com colspan (estado vazio)
            if ($t.find('tbody td[colspan]').length) return;
            $t.DataTable({
                paging: false,
                info: false,
                order: [],
                language: idiomaPtBr,
                columnDefs: [{ targets: 'no-sort', orderable: false }]
            });
        });
    }

    // ---------- Mensagens somem sozinhas ----------
    function autoFecharMensagens() {
        setTimeout(function () {
            $('#area-mensagens .alert-msg-success, #area-mensagens .alert-msg-info').fadeOut(400);
        }, 6000);
    }

    $(function () {
        aplicarMascaras();
        aplicarDataTables();
        autoFecharMensagens();
    });
})(jQuery);
